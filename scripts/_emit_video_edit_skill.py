# Emit .cursor/skills/video-edit as UTF-8
from pathlib import Path

ROOT = Path(r"E:\ai-pro\project_agent")
skill_dir = ROOT / ".cursor" / "skills" / "video-edit"
rules_dir = ROOT / ".cursor" / "rules"
skill_dir.mkdir(parents=True, exist_ok=True)
rules_dir.mkdir(parents=True, exist_ok=True)

zh_cut = "\u89c6\u9891\u526a\u8f91"
zh_sub = "\u5b57\u5e55"
zh_wm = "\u53bb\u6c34\u5370"
zh_tr = "\u8f6c\u573a"
zh_buzz = "\u561f\u561f\u561f"

lines = []
a = lines.append

a("---")
a("name: video-edit")
a("description: >-")
a("  Short-form video editing for project_agent: TTS-synced Chinese subtitles,")
a("  watermark crop, dialogue clips, transitions, and skill cards. Use when the")
a("  user asks to cut/edit/export MP4, add or sync subtitles, remove watermarks,")
a(
    f"  splice clips, make an opening/intro video, or mentions {zh_cut} / {zh_sub} /"
)
a(
    f"  {zh_wm} / {zh_tr} / edge-tts / ffmpeg. Prefer the local Python pipeline; use"
)
a("  Remotion only when the user wants Studio/React compositions.")
a("---")
a("")
a("# Video Edit (project_agent)")
a("")
a("## Choose a stack")
a("")
a("| Need | Stack |")
a("|------|--------|")
a("| Export MP4 quickly (subtitle + TTS + crop + concat) | **Python pipeline** below |")
a(
    "| Interactive Studio / React timeline | Remotion: read "
    "`C:/Users/liste/.codex/skills/remotion-best-practices/SKILL.md` |"
)
a("")
a("Default for this repo: **Python pipeline**.")
a("")
a("## Environment")
a("")
a("- Python: `.venv/Scripts/python.exe`")
a("- FFmpeg: via `imageio_ffmpeg` (no system ffmpeg required)")
a("- Packages: `cv2`, `Pillow`, `edge-tts`, `imageio-ffmpeg`, `numpy`")
a("- Fonts: `C:/Windows/Fonts/msyhbd.ttc`, `msyh.ttc`")
a("- Assets: `img/*.mp4`")
a("- Output: `output/*.mp4`")
a("- Preview frames: `img/_preview_frames/`")
a("")
a("```bash")
a(".venv/Scripts/python.exe -m pip install edge-tts imageio-ffmpeg")
a("```")
a("")
a("## Canonical script")
a("")
a("- Source of truth: `scripts/_write_intro.py` (emits UTF-8 builder)")
a("- Builder: `scripts/make_ge_wechat_intro.py`")
a("- Run:")
a("")
a("```bash")
a(".venv/Scripts/python.exe scripts/_write_intro.py")
a(".venv/Scripts/python.exe scripts/make_ge_wechat_intro.py")
a("```")
a("")
a("Edit dialogue / crop / timing in `_write_intro.py`, regenerate, then rebuild.")
a("")
a("## Hard rules")
a("")
a(
    "1. **One continuous audio timeline** - edge-tts per line to WAV, concat WAVs "
    "+ silence, mux once. Do not concat many short MP4s with separate AAC "
    "(audio dies after line 1)."
)
a("2. **Stream frames** - VideoWriter per frame; never keep full-clip frame lists (OOM).")
a("3. **Subtitles** - spoken text only; no speaker prefixes unless asked.")
a("4. **Watermark** - crop edges (`CROP_*`); never paint a full-width dark veil.")
a("5. **TTS sync** - duration follows TTS; shorten to dialogue pace.")
a(
    '6. **Encoding** - Chinese as unicode escapes in generator; '
    'Path.write_text(..., encoding="utf-8").'
)
a(
    f"7. **Skill VO** - if buzz/{zh_buzz}, use silence or Chinese-only + "
    "highpass/lowpass."
)
a("8. **Verify** - per-second audio RMS must be non-zero through dialogue.")
a("")
a("## Voices")
a("")
a("- Reporter: `zh-CN-XiaoxiaoNeural`")
a("- Deadpan male: `zh-CN-YunjianNeural` (slightly slower)")
a("")
a("## Effects")
a("")
a('- Refusal shake: horizontal sine warpAffine (`effect="shake"`); avoid nodding source.')
a("- Transition: short zoom-flash into skill card (~0.9s).")
a("")
a("## Remotion path")
a("")
a("1. Read Remotion best-practices SKILL.md")
a("2. Scaffold only in empty/new subfolder")
a("3. Open Studio before heavy edits; render only when user asks for MP4")
a("")
a("## More")
a("")
a("See [reference.md](reference.md).")
a("")

(skill_dir / "SKILL.md").write_text("\n".join(lines), encoding="utf-8")

ref = """# Video Edit Reference

## Pipeline

```
edge-tts (per line) -> wav (+ pad)
source mp4 -> crop_clean -> optional shake -> draw_subtitle -> VideoWriter
concat wavs + silence -> align to frame count
mux dialogue.mp4
build tail (transition + skill card) + silent/clean audio
ffmpeg filter concat -> output/ge-wechat-intro.mp4
```

## Current defaults

- Size: 1280x720 @ 30fps
- Crop (Douyin / hardsubs): L260 T100 R270 B155
- Gap between lines: 0.22s
- Transition: 0.9s, skill card: 5.5s
- Example output: `output/ge-wechat-intro.mp4`

## Request map

| Request | Change |
|---------|--------|
| Audio missing after first line | Single-timeline WAV concat; check RMS |
| Remove speaker labels | Subtitle text only |
| Shake head / no nod | `effect=\"shake\"` + better `src_start` |
| Bottom mask bar | Remove veil; raise `CROP_B` / `CROP_R` |
| Shorter runtime | TTS-driven durations only |
| Skill VO noise | Mute skill audio or filter Chinese TTS |
| New source clip | Set `SRC` in `_write_intro.py` |

## Remotion docs

- Router: `~/.codex/skills/remotion-best-practices/SKILL.md`
- Multi-scene: `remotion-markup/multi-scene-video.md`
- Transitions: `remotion-markup/transitions.md`
"""
(skill_dir / "reference.md").write_text(ref, encoding="utf-8")

rule = """---
description: Route video editing tasks to the project video-edit skill
globs:
  - img/**/*.mp4
  - output/**/*.mp4
  - scripts/**/*intro*.py
  - scripts/**/*video*.py
  - .cursor/skills/video-edit/**
alwaysApply: false
---

# Video editing

When the user asks to cut, subtitle, watermark-remove, splice, TTS-sync, or export short videos:

1. Read and follow `.cursor/skills/video-edit/SKILL.md`
2. Prefer the Python pipeline in `scripts/_write_intro.py` + `scripts/make_ge_wechat_intro.py`
3. Use Remotion only if they want Studio/React compositions (then load the Remotion best-practices skill)
"""
(rules_dir / "video-edit.mdc").write_text(rule, encoding="utf-8")

text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
assert zh_cut in text and zh_sub in text
print("OK", skill_dir)
print("SKILL.md", (skill_dir / "SKILL.md").stat().st_size)
print("reference.md", (skill_dir / "reference.md").stat().st_size)
print("rule", (rules_dir / "video-edit.mdc").stat().st_size)
