"""
文档语义分块器（Markdown 标题优先 + 递归字符兜底）
设计说明：
- 我的分块策略是「标题路径 + 15% overlap + 300~800 字区间」，chunk 前拼 `【标题】` 再编码，
  保证向量能感知章节归属，检索时不会出现"命中的 chunk 不知道属于哪一章"。
- 对 PDF/非结构化文本先转 Markdown 再用同一套分块器，避免多格式维护两套逻辑。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import markdownify
from loguru import logger
from pypdf import PdfReader

# 标题正则：支持 # ## ### + HTML <h1>/<h2>/<h3> 形式
_H_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


@dataclass
class Chunk:
    content: str                    # 正文（不含 title_path，调用方自行拼接）
    title_path: List[str] = field(default_factory=list)   # ['一级标题','二级','三级']
    index: int = 0                  # 在整份文档中的序号（0-based）
    file_title: str = ""            # 来源文件名（去扩展名）

    @property
    def breadcrumb(self) -> str:
        return " / ".join(self.title_path)

    def encode_key(self, *, prefix: str = "") -> str:
        """拼接后用于 Embedding 的完整字符串"""
        if self.title_path:
            return f"{prefix}【{self.breadcrumb}】{self.content}"
        return f"{prefix}{self.content}"


def split_markdown(md: str, *, file_title: str = "",
                   chunk_size: int = 600, chunk_overlap: float = 0.15) -> List[Chunk]:
    """按 Markdown 标题做语义分块，再对超长段落递归切字。"""
    lines = md.splitlines()
    stack: List[tuple[int, str]] = []     # [(level, text), ...]
    sections: List[tuple[List[str], List[str]]] = []   # (title_path, lines_in_section)
    current_lines: List[str] = []
    current_path: List[str] = []

    def push_current():
        if current_lines or current_path:
            sections.append((list(current_path), list(current_lines)))

    for raw in lines:
        line = raw.rstrip()
        m = _H_RE.match(line.strip())
        if m:
            push_current()
            current_lines.clear()
            level = len(m.group(1))
            text = m.group(2).strip()
            # 弹出同级或更低级的
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, text))
            current_path = [s[1] for s in stack]
        else:
            current_lines.append(line)
    push_current()

    # 合并空 section（顶层正文）
    merged: List[tuple[List[str], str]] = []
    for path, ls in sections:
        body = "\n".join(ls).strip()
        if not body and not path:
            continue
        merged.append((path, body))

    chunks: List[Chunk] = []
    overlap_chars = max(40, int(chunk_size * chunk_overlap))
    idx = 0
    for path, body in merged:
        if not body:
            # 纯标题（章节开场）：也建一个空正文 chunk，保证检索"章节名"也能命中
            chunks.append(Chunk(
                content="",
                title_path=list(path),
                index=idx,
                file_title=file_title,
            ))
            idx += 1
            continue
        # 超长段落按字符区间切
        if len(body) <= chunk_size:
            chunks.append(Chunk(content=body, title_path=list(path),
                                index=idx, file_title=file_title))
            idx += 1
        else:
            start = 0
            while start < len(body):
                end = min(len(body), start + chunk_size)
                # 尽量停在句号/换行（优雅截断）
                if end < len(body):
                    brk = max(body.rfind("\n", start, end), body.rfind("。", start, end))
                    if brk - start > chunk_size * 0.5:
                        end = brk + 1
                piece = body[start:end].strip()
                if piece:
                    chunks.append(Chunk(content=piece, title_path=list(path),
                                        index=idx, file_title=file_title))
                    idx += 1
                start = max(end - overlap_chars, start + 1)
    logger.info(f"[Splitter] file={file_title} chunks={len(chunks)} size≈{sum(len(c.content) for c in chunks)}")
    return chunks


def load_text_file(path: Path) -> str:
    """自动识别 .md / .txt / .pdf → 归一化为 Markdown 字符串"""
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown", ".txt"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        pages_html: list[str] = []
        for i, page in enumerate(reader.pages):
            txt = page.extract_text() or ""
            pages_html.append(f"<h1>第{i+1}页</h1>\n<p>{txt}</p>")
        md = markdownify.markdownify("\n".join(pages_html), heading_style="ATX")
        return md
    raise ValueError(f"[Splitter] 暂不支持的文件类型: {path.suffix}")
