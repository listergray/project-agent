"""Serialize profile access, with FIFO publishing ahead of background probes."""
from __future__ import annotations

import threading
import time
from collections import deque


class BrowserGate:
    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._holder = ""
        self._publishes: deque[object] = deque()

    def status(self) -> dict:
        with self._condition:
            return {
                "busy": bool(self._holder),
                "holder": self._holder or None,
                "waitingPublish": len(self._publishes),
            }

    def enqueue_publish(self) -> object:
        ticket = object()
        with self._condition:
            self._publishes.append(ticket)
            self._condition.notify_all()
        return ticket

    def acquire_publish(self, ticket: object) -> bool:
        with self._condition:
            if self._holder or not self._publishes or self._publishes[0] is not ticket:
                return False
            self._publishes.popleft()
            self._holder = "publish"
            return True

    def cancel_publish(self, ticket: object) -> None:
        with self._condition:
            if ticket in self._publishes:
                self._publishes.remove(ticket)
                self._condition.notify_all()

    def acquire(self, holder: str, *, wait_sec: float = 0) -> bool:
        deadline = time.monotonic() + max(0, wait_sec)
        with self._condition:
            while self._holder or self._publishes:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                self._condition.wait(remaining)
            self._holder = holder
            return True

    def release(self) -> None:
        with self._condition:
            self._holder = ""
            self._condition.notify_all()
