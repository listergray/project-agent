from __future__ import annotations

import re
from pathlib import Path
from typing import Any


VIDEO_EXTS = {".mp4"}
# e.g. 技术栈EP.32教程.mp4
EP_MP4_RE = re.compile(r"EP\.(\d+)", re.IGNORECASE)

COVER_V_CANDIDATES = (
    "封面上传版_3比4.png",
    "封面上传版_3比4.jpg",
)
COVER_H_CANDIDATES = (
    "封面上传版_4比3.png",
    "封面上传版_4比3.jpg",
)
COVER_FALLBACK = (
    "封面.png",
    "封面.jpg",
    "封面.jpeg",
    "cover.png",
    "cover.jpg",
)

TITLE_CANDIDATES = (
    "标题.txt",
    "标题.md",
    "title.txt",
)

# Fixed hashtags appended to 作品简介
DEFAULT_HASHTAGS = ("#ai编程", "#干货")


def ep_number(name: str) -> int | None:
    m = EP_MP4_RE.search(name)
    if not m:
        return None
    return int(m.group(1))


def scan_videos(
    directory: str,
    min_ep: int | None = None,
    *,
    exclude_published: bool = True,
) -> list[dict[str, Any]]:
    from app.config import settings

    if min_ep is None:
        try:
            from app import db as episode_db

            min_ep = episode_db.get_min_ep()
        except Exception:
            min_ep = settings.min_ep

    done: set[int] = set()
    if exclude_published:
        try:
            from app import db as episode_db

            done = episode_db.published_eps()
        except Exception:
            done = set()

    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"目录不存在: {root}")

    items: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in VIDEO_EXTS:
            continue
        if path.name.startswith("."):
            continue
        num = ep_number(path.name)
        if num is None or num < min_ep:
            continue
        if num in done:
            continue
        meta = resolve_sidecar(path)
        items.append(
            {
                "name": path.name,
                "path": str(path),
                "size": path.stat().st_size,
                "mtime": int(path.stat().st_mtime * 1000),
                "title": meta["title"],
                "titleSource": meta["titleSource"],
                "coverPath": meta["coverPath"],
                "coverPathV": meta["coverPathV"],
                "coverPathH": meta["coverPathH"],
                "description": meta["description"],
                "srtPath": meta["srtPath"],
                "ep": num,
                "relativeDir": str(path.parent.relative_to(root)),
            }
        )
    return items


def resolve_sidecar(video: Path) -> dict[str, Any]:
    """Load title / dual covers / description+hashtags next to the video."""
    parent = video.parent
    title, title_source = _find_title(parent, video)
    cover_v = _find_named(parent, COVER_V_CANDIDATES)
    cover_h = _find_named(parent, COVER_H_CANDIDATES)
    fallback = _find_named(parent, COVER_FALLBACK)
    if not cover_v:
        for ext in (".png", ".jpg", ".jpeg", ".webp"):
            p = video.with_suffix(ext)
            if p.is_file():
                cover_v = p
                break
    if not cover_v:
        cover_v = fallback
    if not cover_h:
        cover_h = fallback
    # Primary coverPath keeps vertical preference for UI list
    cover = cover_v or cover_h
    desc = _build_description(title)
    srt = video.with_suffix(".srt")
    return {
        "title": title,
        "titleSource": title_source,
        "description": desc,
        "coverPath": str(cover) if cover else None,
        "coverPathV": str(cover_v) if cover_v else None,
        "coverPathH": str(cover_h) if cover_h else None,
        "srtPath": str(srt) if srt.is_file() else None,
    }


def _build_description(title: str) -> str:
    from app.config import settings

    tags = settings.publish_hashtag_list or list(DEFAULT_HASHTAGS)
    tag_line = " ".join(tags)
    base = (title or "").strip()
    if not base:
        return tag_line
    if all(t.lstrip("#") in base for t in tags):
        return base[:1000]
    return f"{base}\n{tag_line}"[:1000]


def _find_title(parent: Path, video: Path) -> tuple[str, str]:
    for name in TITLE_CANDIDATES:
        p = parent / name
        if p.is_file():
            text = p.read_text(encoding="utf-8-sig").strip()
            if text:
                line = next((ln.strip() for ln in text.splitlines() if ln.strip()), text)
                return line, name
    same = video.with_suffix(".txt")
    if same.is_file():
        text = same.read_text(encoding="utf-8-sig").strip()
        if text:
            line = next((ln.strip() for ln in text.splitlines() if ln.strip()), text)
            return line, same.name
    return video.stem, "stem"


def _find_named(parent: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        p = parent / name
        if p.is_file():
            return p
    return None
