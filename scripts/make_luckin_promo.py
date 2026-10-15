#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Luckin Coffee Douyin-style selling short video.

from __future__ import annotations

import array
import asyncio
import re
import subprocess
import tempfile
import wave
from pathlib import Path

import cv2
import edge_tts
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(r'E:\ai-pro\project_agent')
OUT = ROOT / 'output' / 'luckin-promo.mp4'
ASSET_HERO = ROOT / 'img' / 'luckin' / 'hero.jpg'
ASSET_LINEUP = ROOT / 'img' / 'luckin' / 'lineup.jpg'
PREVIEW_DIR = ROOT / 'img' / '_preview_frames' / 'luckin_check'

W, H = 1080, 1920
FPS = 30
TARGET_TOTAL_SEC = 8.5
GAP_SEC = 0.05

FONT_BOLD = Path(r'C:\Windows\Fonts\msyhbd.ttc')
FONT_REG = Path(r'C:\Windows\Fonts\msyh.ttc')
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

LINES = [
    (
        'hook',
        '\u745e\u5e78\u7684\u56e4\u8d27\u798f\u5229\u73b0\u5728\u4e0d\u62a2\uff0c\u8fc7\u9635\u5b50\u771f\u7684\u5c31\u6ca1\u4e86',
        'zh-CN-XiaoxiaoNeural',
        '+35%',
    ),
    (
        'value',
        '\u4e00\u767e\u51fa\u5934\u62ff\u5230\u5341\u6b21\u5361\uff0c\u4e8c\u5341\u6b3e\u7ecf\u5178\u996e\u54c1\u968f\u4fbf\u6311',
        'zh-CN-XiaoxiaoNeural',
        '+32%',
    ),
    (
        'taste',
        '\u6bcf\u6b3e\u90fd\u9999\u6d53\u591f\u5473\u8d85\u597d\u559d',
        'zh-CN-XiaoxiaoNeural',
        '+30%',
    ),
    (
        'cta',
        '\u5237\u5230\u5148\u56e4\u53cd\u6b63\u4e0d\u7528\u968f\u65f6\u53ef\u9000\uff0c\u5317\u4eac\u8def\u9644\u8fd1\u7684\u5c0f\u4f19\u4f34\u8d76\u7d27\u51b2',
        'zh-CN-XiaoxiaoNeural',
        '+28%',
    ),
]


def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(str(path), size=size, index=0)
    except OSError:
        return ImageFont.truetype(str(FONT_REG), size=size, index=0)


def audio_duration(path: Path) -> float:
    cmd = [FFMPEG, '-i', str(path), '-f', 'null', '-']
    r = subprocess.run(cmd, capture_output=True, text=True)
    m = re.search(r'Duration:\s*(\d+):(\d+):(\d+\.\d+)', r.stderr)
    if not m:
        raise RuntimeError('cannot probe duration')
    hh, mm, ss = m.groups()
    return int(hh) * 3600 + int(mm) * 60 + float(ss)


async def synth_line(text: str, voice: str, rate: str, out: Path) -> None:
    await edge_tts.Communicate(text, voice=voice, rate=rate).save(str(out))


def to_wav(src: Path, wav: Path, pad_to: float | None = None) -> None:
    af = 'aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo'
    if pad_to is not None:
        af = f'{af},apad=whole_dur={pad_to:.3f}'
    cmd = [FFMPEG, '-y', '-i', str(src), '-af', af, '-ar', '44100', '-ac', '2']
    if pad_to is not None:
        cmd += ['-t', f'{pad_to:.3f}']
    cmd.append(str(wav))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-600:])


def make_silence_wav(path: Path, dur: float) -> None:
    cmd = [
        FFMPEG, '-y', '-f', 'lavfi',
        '-i', f'anullsrc=channel_layout=stereo:sample_rate=44100:duration={dur:.3f}',
        '-c:a', 'pcm_s16le', str(path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def concat_wavs(parts: list[Path], out: Path) -> None:
    lst = out.with_suffix('.txt')
    lst.write_text('\n'.join(f"file '{p.as_posix()}'" for p in parts) + '\n', encoding='utf-8')
    cmd = [
        FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', str(lst),
        '-c', 'pcm_s16le', '-ar', '44100', '-ac', '2', str(out),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-600:])
    lst.unlink(missing_ok=True)


def cover_image(path: Path, progress: float = 0.0) -> Image.Image:
    img = Image.open(path).convert('RGB')
    scale = 1.08 + 0.06 * progress
    nw, nh = int(W * scale), int(H * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    x0 = (nw - W) // 2 + int((nw - W) * 0.08 * (progress - 0.5))
    y0 = (nh - H) // 2
    return img.crop((x0, y0, x0 + W, y0 + H))


def wrap_text(draw, text: str, font, max_w: int) -> list[str]:
    lines: list[str] = []
    cur = ''
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
    return lines


def draw_subtitle(base: Image.Image, text: str) -> np.ndarray:
    img = base.convert('RGBA')
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = load_font(FONT_BOLD, 52)
    lines = wrap_text(draw, text, font, int(W * 0.88))
    line_h = 66
    pad_x, pad_y = 28, 18
    block_h = line_h * len(lines) + pad_y * 2
    block_w = max(draw.textbbox((0, 0), ln, font=font)[2] for ln in lines) + pad_x * 2
    x0 = (W - block_w) // 2
    y0 = H - block_h - 120
    draw.rounded_rectangle([x0, y0, x0 + block_w, y0 + block_h], radius=20, fill=(0, 0, 0, 160))
    for i, ln in enumerate(lines):
        bbox = draw.textbbox((0, 0), ln, font=font)
        tw = bbox[2] - bbox[0]
        tx = (W - tw) // 2
        ty = y0 + pad_y + i * line_h
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            draw.text((tx + dx, ty + dy), ln, font=font, fill=(0, 0, 0, 220))
        draw.text((tx, ty), ln, font=font, fill=(255, 255, 255, 255))
    out = Image.alpha_composite(img, overlay).convert('RGB')
    return cv2.cvtColor(np.array(out), cv2.COLOR_RGB2BGR)


def draw_badge(draw, text: str, y: int, color=(0, 82, 217, 235)) -> None:
    font = load_font(FONT_BOLD, 44)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    pad_x, pad_y = 26, 14
    x0 = (W - tw) // 2 - pad_x
    draw.rounded_rectangle(
        [x0, y, x0 + tw + pad_x * 2, y + (bbox[3] - bbox[1]) + pad_y * 2],
        radius=28,
        fill=color,
    )
    draw.text((x0 + pad_x, y + pad_y - 2), text, font=font, fill=(255, 255, 255, 255))


def make_scene_frame(scene: str, t: float, dur: float, subtitle: str) -> np.ndarray:
    p = min(1.0, t / max(dur, 0.001))
    if scene == 'hook':
        base = cover_image(ASSET_HERO, p)
        base = ImageEnhance.Color(base).enhance(1.15)
        overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        for y in range(420):
            aa = int(160 * (1 - y / 420))
            d.line([(0, y), (W, y)], fill=(10, 40, 120, aa))
        title_font = load_font(FONT_BOLD, 72)
        title = '\u745e\u5e78\u56e4\u8d27\u798f\u5229'
        tb = d.textbbox((0, 0), title, font=title_font)
        d.text(((W - (tb[2] - tb[0])) // 2, 160), title, font=title_font, fill=(255, 255, 255, 255))
        draw_badge(d, '\u8fc7\u671f\u771f\u7684\u5c31\u6ca1\u4e86', 280, (220, 38, 38, 235))
        base = Image.alpha_composite(base.convert('RGBA'), overlay).convert('RGB')
    elif scene == 'value':
        base = cover_image(ASSET_LINEUP, p)
        overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        for y in range(500):
            aa = int(150 * (1 - y / 500))
            d.line([(0, y), (W, y)], fill=(0, 50, 140, aa))
        big = load_font(FONT_BOLD, 78)
        t1 = '20\u90091 \u5341\u6b21\u5361'
        b1 = d.textbbox((0, 0), t1, font=big)
        d.text(((W - (b1[2] - b1[0])) // 2, 140), t1, font=big, fill=(255, 255, 255, 255))
        draw_badge(d, '\u4e00\u767e\u51fa\u5934 \u8d85\u503c\u5fc5\u56e4', 260, (0, 102, 255, 240))
        base = Image.alpha_composite(base.convert('RGBA'), overlay).convert('RGB')
    elif scene == 'taste':
        base = cover_image(ASSET_HERO, 0.3 + 0.5 * p)
        overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        draw_badge(d, '\u9999\u6d53\u591f\u5473 \u8d85\u597d\u559d', 200, (234, 88, 12, 235))
        base = Image.alpha_composite(base.convert('RGBA'), overlay).convert('RGB')
    else:
        base = cover_image(ASSET_LINEUP, 1.0 - 0.3 * p)
        overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        for y in range(H):
            aa = int(40 + 80 * (y / H))
            d.line([(0, y), (W, y)], fill=(0, 40, 100, aa // 3))
        big = load_font(FONT_BOLD, 70)
        t1 = '\u5237\u5230\u5148\u56e4'
        b1 = d.textbbox((0, 0), t1, font=big)
        d.text(((W - (b1[2] - b1[0])) // 2, 220), t1, font=big, fill=(255, 255, 255, 255))
        draw_badge(d, '\u4e0d\u7528\u968f\u65f6\u53ef\u9000', 340, (16, 185, 129, 240))
        draw_badge(d, '\u5317\u4eac\u8def\u9644\u8fd1\u8d76\u7d27\u51b2', 430, (220, 38, 38, 240))
        store = load_font(FONT_REG, 36)
        st = '\u745e\u5e78\u5496\u5561\uff08\u4e94\u6708\u82b1\u5e7f\u573a\u5e97\uff09'
        sb = d.textbbox((0, 0), st, font=store)
        d.text(((W - (sb[2] - sb[0])) // 2, 540), st, font=store, fill=(230, 240, 255, 230))
        base = Image.alpha_composite(base.convert('RGBA'), overlay).convert('RGB')
    if p < 0.12:
        flash = Image.new('RGB', (W, H), (255, 255, 255))
        base = Image.blend(base, flash, 0.25 * (1 - p / 0.12))
    return draw_subtitle(base, subtitle)


def mux(video: Path, audio: Path, out: Path) -> None:
    tmp = out.with_name(out.stem + '_building.mp4')
    cmd = [
        FFMPEG, '-y', '-i', str(video), '-i', str(audio),
        '-map', '0:v:0', '-map', '1:a:0',
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18',
        '-c:a', 'aac', '-ar', '44100', '-ac', '2', '-b:a', '192k',
        '-shortest', '-movflags', '+faststart', '-pix_fmt', 'yuv420p', str(tmp),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-800:])
    tmp.replace(out)


def atempo_chain(speed: float) -> str:
    parts: list[str] = []
    s = speed
    while s > 2.0 + 1e-6:
        parts.append('atempo=2.0')
        s /= 2.0
    while s < 0.5 - 1e-6:
        parts.append('atempo=0.5')
        s /= 0.5
    parts.append(f'atempo={s:.6f}')
    return ','.join(parts)


def compress_to_target(src: Path, out: Path, target: float) -> None:
    dur = audio_duration(src)
    if abs(dur - target) < 0.08:
        if src.resolve() != out.resolve():
            src.replace(out)
        return
    speed = dur / target
    print(f'   compress {dur:.2f}s -> {target:.2f}s (x{speed:.2f})')
    tmp = out.with_name(out.stem + '_speed.mp4')
    fc = f'[0:v]setpts=PTS/{speed:.6f}[v];[0:a]' + atempo_chain(speed) + '[a]'
    cmd = [
        FFMPEG, '-y', '-i', str(src),
        '-filter_complex', fc,
        '-map', '[v]', '-map', '[a]',
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18',
        '-c:a', 'aac', '-ar', '44100', '-ac', '2', '-b:a', '192k',
        '-t', f'{target:.3f}', '-movflags', '+faststart', '-pix_fmt', 'yuv420p',
        str(tmp),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-800:])
    tmp.replace(out)


async def synth_all(tmp: Path):
    items = []
    for i, (scene, text, voice, rate) in enumerate(LINES):
        mp3 = tmp / f'line_{i}.mp3'
        await synth_line(text, voice, rate, mp3)
        dur = max(0.7, audio_duration(mp3) + 0.08)
        wav = tmp / f'line_{i}.wav'
        to_wav(mp3, wav, pad_to=dur)
        items.append((scene, text, wav, dur))
        print(f'  tts[{i}] {scene} {dur:.2f}s')
    return items


def build(tmp: Path, items) -> Path:
    vpath = tmp / 'v.mp4'
    writer = cv2.VideoWriter(str(vpath), cv2.VideoWriter_fourcc(*'mp4v'), FPS, (W, H))
    audio_parts: list[Path] = []
    frame_count = 0
    last = None
    try:
        for i, (scene, text, wav, dur) in enumerate(items):
            n = max(1, int(round(dur * FPS)))
            for fi in range(n):
                last = make_scene_frame(scene, fi / FPS, dur, text)
                writer.write(last)
                frame_count += 1
            audio_parts.append(wav)
            if i < len(items) - 1:
                gap_n = max(1, int(round(GAP_SEC * FPS)))
                for _ in range(gap_n):
                    writer.write(last)
                    frame_count += 1
                gap = tmp / f'gap_{i}.wav'
                make_silence_wav(gap, GAP_SEC)
                audio_parts.append(gap)
    finally:
        writer.release()
    apath = tmp / 'a.wav'
    concat_wavs(audio_parts, apath)
    total = frame_count / FPS
    aligned = tmp / 'a_aligned.wav'
    to_wav(apath, aligned, pad_to=total)
    out = tmp / 'raw.mp4'
    mux(vpath, aligned, out)
    return out


def export_previews(video: Path) -> None:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or FPS
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    dur = n / max(fps, 1)
    for t in [0.3, 2.0, 4.0, 6.0, max(0.5, dur - 0.5)]:
        i = min(n - 1, int(t * fps))
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, f = cap.read()
        if ok:
            p = PREVIEW_DIR / f'p_{int(t * 10):03d}.jpg'
            cv2.imwrite(str(p), f)
            print('preview', p)
    cap.release()


def main() -> None:
    if not ASSET_HERO.exists() or not ASSET_LINEUP.exists():
        raise SystemExit('missing luckin assets under img/luckin/')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    print('out:', OUT)
    with tempfile.TemporaryDirectory(prefix='luckin_') as td:
        tmp = Path(td)
        print('1/3 TTS...')
        items = asyncio.run(synth_all(tmp))
        print('2/3 build scenes...')
        raw = build(tmp, items)
        print('3/3 compress...')
        compress_to_target(raw, OUT, TARGET_TOTAL_SEC)
    probe = OUT.parent / '_probe_luckin.wav'
    subprocess.run(
        [FFMPEG, '-y', '-i', str(OUT), '-ac', '1', '-ar', '16000', str(probe)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    with wave.open(str(probe), 'rb') as w:
        data = array.array('h')
        data.frombytes(w.readframes(w.getnframes()))
        rate = w.getframerate()
    print('audio rms / sec:')
    for i in range(0, len(data), rate):
        chunk = data[i : i + rate]
        if not chunk:
            break
        rms = (sum(x * x for x in chunk) / len(chunk)) ** 0.5
        print(f'  {i / rate:5.1f}s  rms={rms:7.1f}')
    probe.unlink(missing_ok=True)
    export_previews(OUT)
    cap = cv2.VideoCapture(str(OUT))
    fps = cap.get(cv2.CAP_PROP_FPS) or FPS
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    print(f'done: {OUT} ({OUT.stat().st_size / 1024 / 1024:.1f} MB, {n / fps:.1f}s)')


if __name__ == '__main__':
    main()
