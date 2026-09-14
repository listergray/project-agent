"""Markdown / 附件图片抽取，供立项解析把图片内文字并入文档。"""
from __future__ import annotations

import base64
import hashlib
import mimetypes
import re
import urllib.parse
import zipfile
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from loguru import logger

_IMG_MD = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)", re.DOTALL)
_IMG_HTML = re.compile(
    r"<img[^>]+src\s*=\s*[\"']([^\"']+)[\"'][^>]*>",
    re.IGNORECASE | re.DOTALL,
)
# Obsidian / wiki：![[img.png]]、![[folder/a.png|别名]]、![[a.png#fragment]]
_IMG_WIKI = re.compile(r"!\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
# 引用式：![alt][id]  +  [id]: url
_IMG_REF_USE = re.compile(r"!\[([^\]]*)\]\[([^\]]+)\]")
_IMG_REF_DEF = re.compile(r"^\s*\[([^\]]+)\]:\s*(\S.*?)\s*$", re.MULTILINE)
# 全文扫描内嵌 data URL（容忍 base64 换行，不依赖括号）
_DATA_URL_ANY = re.compile(
    r"data:(image/[a-zA-Z0-9.+-]+);base64,([A-Za-z0-9+/=\s]{64,})",
    re.IGNORECASE,
)
_DATA_URL = re.compile(
    r"^data:(image/[a-zA-Z0-9.+-]+);base64,(.+)$",
    re.DOTALL | re.IGNORECASE,
)

_MAX_IMAGES = 8
_MAX_IMAGE_BYTES = 8 * 1024 * 1024


def _guess_mime(path: Path, raw: bytes) -> str:
    mime, _ = mimetypes.guess_type(path.name)
    if mime and mime.startswith("image/"):
        return mime
    if raw[:8].startswith(b"\x89PNG"):
        return "image/png"
    if raw[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if raw[:4] == b"GIF8":
        return "image/gif"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"


def _content_key(raw: bytes) -> str:
    return hashlib.sha1(raw[:4096] + str(len(raw)).encode()).hexdigest()


def _parse_md_dest(raw: str) -> str:
    """解析 Markdown 图片目标：支持 <path>、path \"title\"、URL 编码。"""
    s = (raw or "").strip()
    if not s:
        return ""
    if s.startswith("<"):
        end = s.find(">")
        if end > 0:
            s = s[1:end].strip()
    else:
        # destination 后可选 title：path "title" / path 'title'
        parts = re.split(r"""\s+(?=["'])""", s, maxsplit=1)
        s = parts[0].strip().strip("\"'")
    s = s.replace("file:///", "").replace("file://", "")
    try:
        s = urllib.parse.unquote(s)
    except Exception:  # noqa: BLE001
        pass
    return s.strip()


def _load_data_url(url: str) -> Tuple[str, bytes] | None:
    s = (url or "").strip()
    # 去掉可能包住的 <>、引号、空白
    s = s.strip().strip("<>\"'")
    m = _DATA_URL.match(s)
    if not m:
        # 允许前缀杂质
        m2 = re.search(
            r"data:(image/[a-zA-Z0-9.+-]+);base64,([A-Za-z0-9+/=\s]+)",
            s,
            re.IGNORECASE | re.DOTALL,
        )
        if not m2:
            return None
        mime, b64 = m2.group(1), m2.group(2)
    else:
        mime, b64 = m.group(1), m.group(2)
    # 编辑器常把 base64 折行，必须去掉空白
    b64 = re.sub(r"\s+", "", b64)
    if len(b64) < 32:
        return None
    try:
        raw = base64.b64decode(b64, validate=False)
    except Exception:  # noqa: BLE001
        return None
    if not raw or len(raw) > _MAX_IMAGE_BYTES:
        return None
    # 简单魔数校验，避免解出垃圾
    if not (
        raw.startswith(b"\x89PNG")
        or raw[:3] == b"\xff\xd8\xff"
        or raw[:4] == b"GIF8"
        or (raw[:4] == b"RIFF" and raw[8:12] == b"WEBP")
        or raw[:2] in (b"BM",)
    ):
        # 仍可能是合法图，放宽：只要够大就用
        if len(raw) < 64:
            return None
    return mime.lower(), raw


def _load_path(src: str, base_dirs: Sequence[Path]) -> Tuple[str, bytes, str] | None:
    src = _parse_md_dest(src)
    if not src:
        return None
    if src.startswith(("http://", "https://")):
        return None  # 远程图 MVP 不拉，避免 SSRF
    data = _load_data_url(src)
    if data:
        mime, raw = data
        return mime, raw, "embedded"
    path = Path(src)
    candidates: List[Path] = []
    if path.is_absolute():
        candidates.append(path)
    else:
        for base in base_dirs:
            candidates.append((base / path).resolve())
            candidates.append((base / path.name).resolve())
            # 常见附件目录兜底
            for sub in ("assets", "images", "attachments", "media", "static"):
                candidates.append((base / sub / path.name).resolve())
    for cand in candidates:
        try:
            if not cand.is_file():
                continue
            raw = cand.read_bytes()
            if not raw or len(raw) > _MAX_IMAGE_BYTES:
                continue
            return _guess_mime(cand, raw), raw, cand.name
        except Exception:  # noqa: BLE001
            continue
    return None


def _iter_image_refs(text: str) -> List[Tuple[str, str]]:
    """返回 [(label, src), ...]，含 md / html / obsidian / 引用式 / 裸 data-url。"""
    refs: List[Tuple[str, str]] = []
    body = text or ""

    for alt, src in _IMG_MD.findall(body):
        refs.append((alt.strip(), src))
    for src in _IMG_HTML.findall(body):
        refs.append(("", src))
    for src in _IMG_WIKI.findall(body):
        refs.append(("", src.strip()))

    defs = {k.strip(): v.strip() for k, v in _IMG_REF_DEF.findall(body)}
    for alt, key in _IMG_REF_USE.findall(body):
        dest = defs.get(key.strip()) or defs.get(key.strip().lower())
        if dest:
            refs.append((alt.strip(), dest))

    # 再扫一遍全文 data:image，防止括号截断/特殊写法漏网
    seen_data = {(_parse_md_dest(s) or s)[:64] for _, s in refs if "data:image" in (s or "").lower()}
    for mime, b64 in _DATA_URL_ANY.findall(body):
        data_url = f"data:{mime};base64,{re.sub(r'\s+', '', b64)}"
        key = data_url[:64]
        if key in seen_data:
            continue
        seen_data.add(key)
        refs.append(("embedded", data_url))

    return refs


def collect_markdown_images(
    text: str,
    *,
    base_dirs: Sequence[Path] | None = None,
) -> Tuple[List[Tuple[str, bytes, str]], List[str]]:
    """返回 ([(mime, bytes, label), ...], missing_refs)。"""
    bases = list(base_dirs or [])
    found: List[Tuple[str, bytes, str]] = []
    missing: List[str] = []
    seen: set[str] = set()

    def _add(mime: str, raw: bytes, label: str) -> None:
        key = _content_key(raw)
        if key in seen or len(found) >= _MAX_IMAGES:
            return
        seen.add(key)
        found.append((mime, raw, label))

    for alt, src in _iter_image_refs(text):
        dest = _parse_md_dest(src)
        if dest.startswith(("http://", "https://")):
            missing.append(dest[:80])
            continue
        hit = _load_path(src, bases)
        if hit:
            mime, raw, name = hit
            _add(mime, raw, alt or name)
        else:
            if dest.startswith("data:"):
                missing.append("embedded-data-url")
            else:
                missing.append(dest or src[:80])

    return found, missing


def merge_extra_image_files(
    images: Iterable[Tuple[str, bytes]],
    existing: List[Tuple[str, bytes, str]] | None = None,
) -> List[Tuple[str, bytes, str]]:
    out = list(existing or [])
    seen = {_content_key(raw) for _, raw, _ in out}
    for name, raw in images:
        if not raw or len(raw) > _MAX_IMAGE_BYTES or len(out) >= _MAX_IMAGES:
            continue
        path = Path(name)
        mime = _guess_mime(path, raw)
        if not mime.startswith("image/"):
            continue
        key = _content_key(raw)
        if key in seen:
            continue
        seen.add(key)
        out.append((mime, raw, path.name))
    return out


def unpack_zip_doc(zip_path: Path, dest_dir: Path) -> Tuple[Path, Path]:
    """解压 zip，返回 (主文档路径, 解压根目录)。"""
    from project_agent.projects.doc_extract import zip_preferred_docs

    dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)
    prefer = list(zip_preferred_docs())
    rank = {ext: i for i, ext in enumerate(prefer)}
    docs = []
    for p in dest_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in rank:
            docs.append(p)
    if not docs:
        raise ValueError("压缩包内未找到 .md / .docx / .xlsx / .pdf / .txt")
    docs.sort(key=lambda p: (rank.get(p.suffix.lower(), 99), len(str(p))))
    return docs[0], dest_dir


def _ocr_local(raw: bytes) -> str:
    """本地 OCR 兜底（无需多模态 LLM）。依赖可选：rapidocr-onnxruntime + pillow。"""
    try:
        from io import BytesIO

        import numpy as np
        from PIL import Image
        from rapidocr_onnxruntime import RapidOCR
    except Exception as e:  # noqa: BLE001
        logger.debug(f"[Projects] 本地 OCR 不可用: {e}")
        return ""

    try:
        img = Image.open(BytesIO(raw)).convert("RGB")
        arr = np.array(img)
        engine = RapidOCR()
        result, _ = engine(arr)
        if not result:
            return ""
        lines = []
        for item in result:
            # item: [box, text, score]
            if len(item) >= 2 and item[1]:
                lines.append(str(item[1]).strip())
        return "\n".join(x for x in lines if x)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[Projects] 本地 OCR 失败: {e}")
        return ""


def _vision_configured() -> bool:
    """未单独配置多模态模型时不走文本 LLM（DeepSeek chat 无视觉，易慢/空）。"""
    try:
        from project_agent.core import get_settings

        return bool((get_settings().llm_vision_model or "").strip())
    except Exception:  # noqa: BLE001
        return False


def vision_extract_text(mime: str, raw: bytes, *, label: str = "") -> str:
    """有多模态配置时优先 LLM，否则/失败则本地 OCR。"""
    text = ""
    if _vision_configured():
        try:
            from project_agent.clients.llm_client import vision_achain

            b64 = base64.b64encode(raw).decode("ascii")
            data_url = f"data:{mime};base64,{b64}"
            prompt = (
                "这是立项/需求文档中的截图或插图。请完整提取图中所有文字（表格、键值、标题、段落），"
                "按原文顺序输出纯文本；不要解释、不要翻译。若几乎无文字，返回空。"
            )
            if label:
                prompt = f"图片说明/文件名: {label}\n{prompt}"
            text = (vision_achain(prompt, data_url) or "").strip()
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[Projects] 多模态提取失败 label={label!r}: {e}")

    if text:
        return text

    local = _ocr_local(raw)
    if local:
        logger.info(f"[Projects] 使用本地 OCR label={label!r} chars={len(local)}")
    return local


def enrich_text_with_images(
    text: str,
    *,
    base_dirs: Sequence[Path] | None = None,
    extra_images: Sequence[Tuple[str, bytes]] | None = None,
) -> Tuple[str, int, List[str]]:
    """
    把图片 OCR/视觉结果并入文档文本。
    重要：会剥掉 md 内巨型 base64，避免 parse 时 12k 截断把 OCR 结果裁掉。
    返回 (enriched_text, image_ok_count, warnings)
    """
    warnings: List[str] = []
    body = text or ""
    imgs, missing = collect_markdown_images(body, base_dirs=base_dirs)
    if extra_images:
        imgs = merge_extra_image_files(extra_images, imgs)

    if missing:
        shown = "、".join(missing[:5])
        more = f" 等{len(missing)}处" if len(missing) > 5 else ""
        warnings.append(
            f"文档引用了图片但未找到文件: {shown}{more}。"
            "不必打包：请将图片与 .md 一并多选上传（或图已内嵌 base64 可只传 md）"
        )

    # 先剥掉内嵌 data URL，换成短占位（否则 base64 占满截断窗口）
    cleaned = _DATA_URL_ANY.sub(lambda m: f"[内嵌图片:{m.group(1)}]", body)
    cleaned = re.sub(
        r"!\[([^\]]*)\]\(\s*data:image\/[^)]+\)",
        lambda m: f"![图:{m.group(1) or 'embedded'}]()",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not imgs:
        return cleaned, 0, warnings

    chunks: List[str] = []
    ok = 0
    for mime, raw, label in imgs:
        extracted = vision_extract_text(mime, raw, label=label)
        if extracted:
            ok += 1
            chunks.append(f"## [图片内容: {label}]\n{extracted}\n")
        else:
            warnings.append(f"未能从图片提取文字: {label}")

    if ok == 0 and imgs:
        warnings.append(
            "文档含图片但未能识别文字（可配置 LLM_VISION_MODEL 提升效果）"
        )

    # OCR 结果放最前面，保证后续 parse 截断时仍能读到
    head = "\n\n".join(chunks).strip()
    if head:
        enriched = f"{head}\n\n---\n\n{cleaned}"
    else:
        enriched = cleaned
    logger.info(f"[Projects] 图片增强: total={len(imgs)} ok={ok} missing={len(missing)}")
    return enriched, ok, warnings
