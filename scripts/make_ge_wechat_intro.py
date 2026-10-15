#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Short Ge Daye intro (TTS synced) + transition + WeChat Ctrl+Win tip.

from __future__ import annotations

import array
import asyncio
import math
import re
import subprocess
import tempfile
import wave
from pathlib import Path

import cv2
import edge_tts
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"E:\ai-pro\project_agent")
SRC = ROOT / "img" / "40366b85d7168a62d71c66233ad07de8.mp4"
OUT = ROOT / "output" / "ge-wechat-intro.mp4"
PREVIEW_DIR = ROOT / "img" / "_preview_frames" / "final_check"

W, H = 1280, 720
FPS = 30
TRANSITION_SEC = 0.4
SKILL_SEC = 1.8
GAP_SEC = 0.06
TARGET_TOTAL_SEC = 8.0

CROP_L, CROP_T, CROP_R, CROP_B = 260, 100, 270, 155

FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")
FONT_REG = Path(r"C:\Windows\Fonts\msyh.ttc")
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# text, src_start, voice, rate, effect
LINES = [
    (
        "\u7ed9\u4f60\u4e00\u4e2a\u4ebf\uff0c\u6559\u6211\u4e2a\u7535\u8111\u6280\u80fd\uff0c\u53ef\u4ee5\u4e48\uff1f",
        10.0,
        "zh-CN-XiaoxiaoNeural",
        "+45%",
        "hold",
    ),
    ("\u4e0d\u53ef\u4ee5", 14.8, "zh-CN-YunjianNeural", "+35%", "shake"),
    (
        "\u90a3\u4e0d\u7ed9\u4f60\u94b1\u5462\uff1f",
        13.0,
        "zh-CN-XiaoxiaoNeural",
        "+45%",
        None,
    ),
    ("\u53ef\u4ee5", 17.8, "zh-CN-YunjianNeural", "+40%", None),
    ("\u4e3a\u4ec0\u4e48\uff1f", 21.5, "zh-CN-XiaoxiaoNeural", "+40%", None),
    (
        "\u56e0\u4e3a\u4f60\u6ca1\u6709\u4e00\u4e2a\u4ebf",
        36.5,
        "zh-CN-YunjianNeural",
        "+30%",
        None,
    ),
]


def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(str(path), size=size, index=0)
    except OSError:
        return ImageFont.truetype(str(FONT_REG), size=size, index=0)


def crop_clean(bgr: np.ndarray) -> np.ndarray:
    h, w = bgr.shape[:2]
    cropped = bgr[CROP_T : h - CROP_B, CROP_L : w - CROP_R]
    scaled = cv2.resize(cropped, (W, H), interpolation=cv2.INTER_LANCZOS4)
    pw, ph = 110, 70
    sample = scaled[ph : ph + 30, 10 : pw + 10].mean(axis=(0, 1))
    roi = scaled[:ph, :pw].astype(np.float32)
    bright = (roi[:, :, 0] > 170) & (roi[:, :, 1] > 170) & (roi[:, :, 2] > 170)
    if bright.any():
        bright_u8 = bright.astype(np.uint8) * 255
        bright_u8 = cv2.dilate(bright_u8, np.ones((5, 5), np.uint8), iterations=1)
        mask = bright_u8 > 0
        for c in range(3):
            ch = roi[:, :, c]
            ch[mask] = sample[c]
            roi[:, :, c] = ch
        scaled[:ph, :pw] = roi.astype(np.uint8)
    return scaled


def draw_subtitle(bgr: np.ndarray, text: str) -> np.ndarray:
    img = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = load_font(FONT_BOLD, 42)

    max_w = int(W * 0.88)
    lines: list[str] = []
    cur = ""
    for ch in text:
        trial = cur + ch
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)

    line_h = 54
    pad_x, pad_y = 22, 12
    block_h = line_h * len(lines) + pad_y * 2
    block_w = max(draw.textbbox((0, 0), ln, font=font)[2] for ln in lines) + pad_x * 2
    x0 = (W - block_w) // 2
    y0 = H - block_h - 28
    draw.rounded_rectangle(
        [x0, y0, x0 + block_w, y0 + block_h],
        radius=12,
        fill=(0, 0, 0, 145),
    )
    for i, ln in enumerate(lines):
        bbox = draw.textbbox((0, 0), ln, font=font)
        tw = bbox[2] - bbox[0]
        tx = (W - tw) // 2
        ty = y0 + pad_y + i * line_h
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            draw.text((tx + dx, ty + dy), ln, font=font, fill=(0, 0, 0, 210))
        draw.text((tx, ty), ln, font=font, fill=(255, 255, 255, 255))

    out = Image.alpha_composite(img, overlay).convert("RGB")
    return cv2.cvtColor(np.array(out), cv2.COLOR_RGB2BGR)


def audio_duration(path: Path) -> float:
    cmd = [FFMPEG, "-i", str(path), "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", r.stderr)
    if not m:
        raise RuntimeError(f"cannot probe duration: {path}\n{r.stderr[-400:]}")
    hh, mm, ss = m.groups()
    return int(hh) * 3600 + int(mm) * 60 + float(ss)


async def synth_line(text: str, voice: str, rate: str, out: Path) -> None:
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.save(str(out))


def to_wav(src: Path, wav: Path, pad_to: float | None = None, extra_af: str = "") -> None:
    af = "aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo"
    if extra_af:
        af = extra_af + "," + af
    if pad_to is not None:
        af = f"{af},apad=whole_dur={pad_to:.3f}"
    cmd = [FFMPEG, "-y", "-i", str(src), "-af", af, "-ar", "44100", "-ac", "2"]
    if pad_to is not None:
        cmd += ["-t", f"{pad_to:.3f}"]
    cmd.append(str(wav))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-600:])


def make_silence_wav(path: Path, dur: float) -> None:
    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=channel_layout=stereo:sample_rate=44100:duration={dur:.3f}",
        "-c:a",
        "pcm_s16le",
        str(path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def concat_wavs(parts: list[Path], out: Path) -> None:
    lst = out.with_suffix(".txt")
    lst.write_text("\n".join(f"file '{p.as_posix()}'" for p in parts) + "\n", encoding="utf-8")
    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(lst),
        "-c",
        "pcm_s16le",
        "-ar",
        "44100",
        "-ac",
        "2",
        str(out),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-600:])
    lst.unlink(missing_ok=True)


def iter_src_frames(src_start: float, n_frames: int):
    """Yield cleaned frames one-by-one to keep memory low."""
    cap = cv2.VideoCapture(str(SRC))
    try:
        src_fps = cap.get(cv2.CAP_PROP_FPS) or FPS
        max_frame = int(41.5 * src_fps)
        start = int(src_start * src_fps)
        start = min(start, max(0, max_frame - n_frames - 1))
        start = max(0, start)
        cap.set(cv2.CAP_PROP_POS_MSEC, (start / src_fps) * 1000.0)
        last = None
        produced = 0
        while produced < n_frames:
            ok, frame = cap.read()
            if not ok:
                break
            last = crop_clean(frame)
            yield last
            produced += 1
            del frame
        if last is None:
            raise RuntimeError(f"no frames at {src_start}s")
        while produced < n_frames:
            yield last
            produced += 1
    finally:
        cap.release()


def apply_head_shake(frames: list[np.ndarray], hz: float = 2.4, amp_px: int = 36) -> list[np.ndarray]:
    out: list[np.ndarray] = []
    for i, fr in enumerate(frames):
        t = i / FPS
        env = math.sin(math.pi * min(1.0, max(0.0, i / max(len(frames) - 1, 1))))
        dx = int(amp_px * env * math.sin(2 * math.pi * hz * t))
        h, w = fr.shape[:2]
        m = np.float32([[1, 0, dx], [0, 1, dx * 0.05]])
        out.append(cv2.warpAffine(fr, m, (w, h), borderMode=cv2.BORDER_REFLECT_101))
    return out


def rounded_key(draw, box, label, font, active: bool) -> None:
    x0, y0, x1, y1 = box
    fill = (56, 189, 248, 255) if active else (40, 44, 52, 255)
    border = (165, 243, 252, 255) if active else (100, 110, 125, 255)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=fill, outline=border, width=3)
    bbox = draw.textbbox((0, 0), label, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = x0 + (x1 - x0 - tw) // 2
    ty = y0 + (y1 - y0 - th) // 2 - 2
    color = (8, 20, 30, 255) if active else (235, 240, 250, 255)
    draw.text((tx, ty), label, font=font, fill=color)


def make_skill_frame(t: float, duration: float) -> np.ndarray:
    progress = t / max(duration, 0.001)
    img = Image.new("RGB", (W, H), (12, 16, 28))
    draw = ImageDraw.Draw(img, "RGBA")
    for y in range(H):
        c = int(12 + 28 * (y / H))
        draw.line([(0, y), (W, y)], fill=(c, c + 4, c + 18))

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    cx = int(W * (0.35 + 0.3 * math.sin(progress * math.pi * 2)))
    gdraw.ellipse([cx - 220, 80, cx + 220, 320], fill=(34, 197, 94, 40))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")

    title_font = load_font(FONT_BOLD, 52)
    sub_font = load_font(FONT_REG, 32)
    key_font = load_font(FONT_BOLD, 40)
    mid_font = load_font(FONT_BOLD, 38)

    title = "\u5fae\u4fe1\u6280\u80fd \u00b7 \u4efb\u610f\u4f4d\u7f6e\u8bed\u97f3\u8f93\u5165"
    tb = draw.textbbox((0, 0), title, font=title_font)
    draw.text(((W - (tb[2] - tb[0])) // 2, 80), title, font=title_font, fill=(255, 255, 255))

    ctrl_on = 0.18 <= progress < 0.42 or progress >= 0.62
    win_on = 0.42 <= progress < 0.62 or progress >= 0.62
    key_w, key_h, gap = 220, 110, 40
    kx = (W - (key_w * 2 + gap)) // 2
    ky = 220
    rounded_key(draw, (kx, ky, kx + key_w, ky + key_h), "Ctrl", key_font, ctrl_on)
    pb = draw.textbbox((0, 0), "+", font=key_font)
    draw.text(
        (kx + key_w + (gap - (pb[2] - pb[0])) // 2, ky + 30),
        "+",
        font=key_font,
        fill=(200, 210, 230),
    )
    rounded_key(
        draw,
        (kx + key_w + gap, ky, kx + key_w + gap + key_w, ky + key_h),
        "Win",
        key_font,
        win_on,
    )

    lines = [
        ("\u6309\u4e0b  Ctrl + Win", mid_font),
        (
            "\u4e0d\u9650\u5fae\u4fe1\u8f93\u5165\u6846 \u2014\u2014 \u7cfb\u7edf\u4efb\u610f\u4f4d\u7f6e\u90fd\u80fd\u8bed\u97f3\u8f6c\u6587\u5b57",
            sub_font,
        ),
        ("\u6253\u5b57\u6162\uff1f\u8bf4\u8bdd\u5c31\u884c", sub_font),
    ]
    y = 390
    for i, (line, font) in enumerate(lines):
        appear = 0.2 + i * 0.12
        alpha = 0 if progress < appear else min(1.0, (progress - appear) / 0.12)
        color = (int(220 * alpha + 30), int(235 * alpha + 30), int(255 * alpha))
        bb = draw.textbbox((0, 0), line, font=font)
        draw.text(((W - (bb[2] - bb[0])) // 2, y), line, font=font, fill=color)
        y += 58 if i else 60

    return cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)


def make_transition_frame(a: np.ndarray, b: np.ndarray, p: float) -> np.ndarray:
    p = float(np.clip(p, 0, 1))
    if p < 0.5:
        t = p / 0.5
        scale = 1 + 0.45 * t
        flash = t**1.5
        h, w = a.shape[:2]
        m = cv2.getRotationMatrix2D((w / 2, h / 2), -6 * t, scale)
        warped = cv2.warpAffine(a, m, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        white = np.full_like(warped, 255)
        return cv2.addWeighted(warped, 1 - flash * 0.8, white, flash * 0.8, 0)
    t = (p - 0.5) / 0.5
    scale = 1.35 - 0.35 * t
    h, w = b.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), 10 * (1 - t), scale)
    warped = cv2.warpAffine(b, m, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    white = np.full_like(warped, 255)
    out = cv2.addWeighted(white, 1 - t, warped, t, 0)
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt((xx - w / 2) ** 2 + (yy - h / 2) ** 2)
    max_r = math.hypot(w / 2, h / 2)
    mask = np.clip((t * 1.15 * max_r - r) / (0.18 * max_r), 0, 1)[..., None]
    return (warped.astype(np.float32) * mask + out.astype(np.float32) * (1 - mask)).astype(np.uint8)


def write_video(frames: list[np.ndarray], path: Path) -> None:
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    for fr in frames:
        writer.write(fr)
    writer.release()


def mux(video: Path, audio: Path, out: Path) -> None:
    tmp = out.with_name(out.stem + "_building.mp4")
    cmd = [
        FFMPEG,
        "-y",
        "-i",
        str(video),
        "-i",
        str(audio),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-crf",
        "18",
        "-c:a",
        "aac",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        "-pix_fmt",
        "yuv420p",
        str(tmp),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-800:])
    tmp.replace(out)


def export_previews(video: Path) -> None:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or FPS
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    dur = n / max(fps, 1)
    for t in [0.5, 3.8, 5.5, 7.5, 10.0, max(0.5, dur - 2.0)]:
        i = min(n - 1, int(t * fps))
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, f = cap.read()
        if ok:
            p = PREVIEW_DIR / f"check_{int(t * 10):03d}.jpg"
            cv2.imwrite(str(p), f)
            print("preview", p, f"t={t:.1f}s")
    cap.release()


async def synth_all(tmp: Path):
    items = []
    for i, (text, src_start, voice, rate, effect) in enumerate(LINES):
        mp3 = tmp / f"line_{i}.mp3"
        await synth_line(text, voice, rate, mp3)
        dur = max(0.75, audio_duration(mp3) + 0.10)
        wav = tmp / f"line_{i}.wav"
        to_wav(mp3, wav, pad_to=dur)
        items.append((text, wav, dur, src_start, effect))
        print(f"  tts[{i}] {dur:.2f}s  effect={effect}")
    return items


def build_dialogue(tmp: Path, items):
    audio_parts: list[Path] = []
    last = None
    frame_count = 0
    vpath = tmp / "dialogue_v.mp4"
    writer = cv2.VideoWriter(str(vpath), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    try:
        for i, (text, wav, dur, src_start, effect) in enumerate(items):
            n = max(1, int(round(dur * FPS)))
            hold_frame = None
            for fi, fr in enumerate(iter_src_frames(src_start, n)):
                if effect == "hold":
                    if hold_frame is None:
                        hold_frame = fr.copy()
                    fr = hold_frame
                elif effect == "shake":
                    t = fi / FPS
                    env = math.sin(math.pi * min(1.0, max(0.0, fi / max(n - 1, 1))))
                    dx = int(36 * env * math.sin(2 * math.pi * 2.4 * t))
                    h, w = fr.shape[:2]
                    m = np.float32([[1, 0, dx], [0, 1, dx * 0.05]])
                    fr = cv2.warpAffine(fr, m, (w, h), borderMode=cv2.BORDER_REFLECT_101)
                last = draw_subtitle(fr, text)
                writer.write(last)
                frame_count += 1
            audio_parts.append(wav)
            if i < len(items) - 1:
                gap_n = max(1, int(round(GAP_SEC * FPS)))
                for _ in range(gap_n):
                    writer.write(last)
                    frame_count += 1
                gap_wav = tmp / f"gap_{i}.wav"
                make_silence_wav(gap_wav, GAP_SEC)
                audio_parts.append(gap_wav)
    finally:
        writer.release()

    assert last is not None
    apath = tmp / "dialogue_a.wav"
    concat_wavs(audio_parts, apath)
    dur = frame_count / FPS
    aligned = tmp / "dialogue_a_aligned.wav"
    cmd = [
        FFMPEG,
        "-y",
        "-i",
        str(apath),
        "-af",
        f"apad=whole_dur={dur:.3f}",
        "-t",
        f"{dur:.3f}",
        str(aligned),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    out = tmp / "dialogue.mp4"
    mux(vpath, aligned, out)
    return out, last, dur


def build_tail(tmp: Path, last_frame: np.ndarray) -> Path:
    skill_frames = int(SKILL_SEC * FPS)
    trans_frames = int(TRANSITION_SEC * FPS)
    first_skill = make_skill_frame(0, SKILL_SEC)
    vpath = tmp / "tail_v.mp4"
    writer = cv2.VideoWriter(str(vpath), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    try:
        for i in range(trans_frames):
            writer.write(
                make_transition_frame(last_frame, first_skill, i / max(trans_frames - 1, 1))
            )
        for i in range(skill_frames):
            writer.write(make_skill_frame(i / FPS, SKILL_SEC))
    finally:
        writer.release()

    # silent skill section (avoid TTS buzz / artifacts)
    total = TRANSITION_SEC + SKILL_SEC
    tip_wav = tmp / "skill_silent.wav"
    make_silence_wav(tip_wav, total)
    out = tmp / "tail.mp4"
    mux(vpath, tip_wav, out)
    return out


def concat_final(a: Path, b: Path, out: Path) -> None:
    tmp = out.with_name(out.stem + "_building.mp4")
    cmd = [
        FFMPEG,
        "-y",
        "-i",
        str(a),
        "-i",
        str(b),
        "-filter_complex",
        "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]",
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-crf",
        "18",
        "-c:a",
        "aac",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        "-pix_fmt",
        "yuv420p",
        str(tmp),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-800:])
    tmp.replace(out)


def atempo_chain(speed: float) -> str:
    """Build atempo filter chain (each stage in 0.5..2.0)."""
    parts: list[str] = []
    s = speed
    while s > 2.0 + 1e-6:
        parts.append("atempo=2.0")
        s /= 2.0
    while s < 0.5 - 1e-6:
        parts.append("atempo=0.5")
        s /= 0.5
    parts.append(f"atempo={s:.6f}")
    return ",".join(parts)


def compress_to_target(src: Path, out: Path, target: float) -> None:
    dur = audio_duration(src)
    if dur <= 0:
        raise RuntimeError("cannot probe duration for compress")
    if abs(dur - target) < 0.05:
        if src != out:
            src.replace(out)
        return
    speed = dur / target
    print(f"   compress {dur:.2f}s -> {target:.2f}s (speed x{speed:.2f})")
    tmp = out.with_name(out.stem + "_speed.mp4")
    vf = f"setpts=PTS/{speed:.6f}"
    af = atempo_chain(speed)
    cmd = [
        FFMPEG,
        "-y",
        "-i",
        str(src),
        "-filter_complex",
        f"[0:v]{vf}[v];[0:a]{af}[a]",
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-crf",
        "18",
        "-c:a",
        "aac",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-b:a",
        "192k",
        "-t",
        f"{target:.3f}",
        "-movflags",
        "+faststart",
        "-pix_fmt",
        "yuv420p",
        str(tmp),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-800:])
    tmp.replace(out)


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"missing source: {SRC}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    print("src:", SRC)
    print("out:", OUT)

    with tempfile.TemporaryDirectory(prefix="ge_intro_") as td:
        tmp = Path(td)
        print("1/4 TTS...")
        items = asyncio.run(synth_all(tmp))

        print("2/4 dialogue (single A/V timeline)...")
        dialogue, last, ddur = build_dialogue(tmp, items)
        print(f"   dialogue {ddur:.1f}s")

        print("3/4 transition + skill...")
        tail = build_tail(tmp, last)

        print("4/5 final concat...")
        concat_final(dialogue, tail, OUT)

        print("5/5 compress to target...")
        compress_to_target(OUT, OUT, TARGET_TOTAL_SEC)

    probe = OUT.parent / "_probe.wav"
    subprocess.run(
        [FFMPEG, "-y", "-i", str(OUT), "-ac", "1", "-ar", "16000", str(probe)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    with wave.open(str(probe), "rb") as w:
        data = array.array("h")
        data.frombytes(w.readframes(w.getnframes()))
        rate = w.getframerate()
    print("audio rms / sec:")
    for i in range(0, len(data), rate):
        chunk = data[i : i + rate]
        if not chunk:
            break
        rms = (sum(x * x for x in chunk) / len(chunk)) ** 0.5
        print(f"  {i / rate:5.1f}s  rms={rms:7.1f}")
    probe.unlink(missing_ok=True)

    export_previews(OUT)
    cap = cv2.VideoCapture(str(OUT))
    fps = cap.get(cv2.CAP_PROP_FPS) or FPS
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    print(f"done: {OUT} ({OUT.stat().st_size / 1024 / 1024:.1f} MB, {n / fps:.1f}s)")


if __name__ == "__main__":
    main()
