"""site-docs PPTX/PDF 생성기 — SiteDocs JSON → .pptx (+soffice PDF).

spec: docs/superpowers/specs/2026-06-24-site-docs-pptx-export-design.md
3 repo byte-identical: cop/hdel dashboard/, hermes scripts/.
"""
from __future__ import annotations

import os
import re

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE

_GRAY = RGBColor(0x6B, 0x72, 0x80)

_RUN_RE = re.compile(r"`([^`]+)`|\*\*([^*]+)\*\*|\[([^\]]+)\]\(([^)]+)\)")
_SCHEME_RE = re.compile(r"^([a-z][a-z0-9+.\-]*):", re.I)
_ALLOWED = re.compile(r"^(https?|mailto)$", re.I)


def inline(text: str) -> list[dict]:
    """뷰어 render-markdown.ts inline() 미러: code / **bold** / [txt](url). 이탤릭 미지원."""
    out: list[dict] = []
    pos = 0
    for m in _RUN_RE.finditer(text):
        if m.start() > pos:
            out.append({"t": "text", "s": text[pos:m.start()]})
        if m.group(1) is not None:                      # `code`
            out.append({"t": "code", "s": m.group(1)})
        elif m.group(2) is not None:                    # **bold**
            out.append({"t": "bold", "s": m.group(2)})
        else:                                           # [txt](url)
            out.append({"t": "link", "s": m.group(3)})  # display text only; url dropped
        pos = m.end()
    if pos < len(text):
        out.append({"t": "text", "s": text[pos:]})
    return out or [{"t": "text", "s": ""}]


_H_RE = re.compile(r"^(#{1,6})\s+(.+)$")
_UL_RE = re.compile(r"^[-*]\s+(.+)$")
_OL_RE = re.compile(r"^\d+\.\s+(.+)$")
_SEP_CELL_RE = re.compile(r"^:?-+:?$")


def _split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _is_table_sep(line: str) -> bool:
    cells = _split_row(line)
    return bool(cells) and all(_SEP_CELL_RE.match(c) for c in cells)


def _runs_text(runs: list[dict]) -> str:
    return "".join(r["s"] for r in runs)


def parse_markdown(md: str) -> list[dict]:
    if not md or not md.strip():
        return [{"type": "empty"}]
    blocks: list[dict] = []
    buf: list[str] = []
    cur_list = None  # ("ulist"|"olist", [items])
    in_code = False
    code_lines: list[str] = []

    def flush_para():
        nonlocal buf
        if buf:
            # join soft-wrapped lines, then strip — mirrors viewer flushBuf's buf.join(' ').trim()
            blocks.append({"type": "para", "runs": inline(" ".join(buf).strip())})
            buf = []

    def flush_list():
        nonlocal cur_list
        if cur_list:
            blocks.append({"type": cur_list[0], "items": cur_list[1]})
            cur_list = None

    lines = md.replace("\r\n", "\n").split("\n")
    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        if in_code:
            if line.strip() == "```":
                blocks.append({"type": "code", "text": "\n".join(code_lines)})
                code_lines = []
                in_code = False
            else:
                code_lines.append(raw)  # preserve leading whitespace; no inline
            i += 1
            continue
        if line.strip() == "```":
            flush_para(); flush_list(); in_code = True; i += 1; continue
        if line.lstrip().startswith("|") and i + 1 < len(lines) and _is_table_sep(lines[i + 1]):
            flush_para(); flush_list()
            header = [inline(c) for c in _split_row(line)]
            ncol = len(header)
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                cells = _split_row(lines[j])
                # normalize each row to header width: drop extras, pad missing (mirrors viewer)
                rows.append([inline(cells[c]) if c < len(cells) else [{"t": "text", "s": ""}]
                             for c in range(ncol)])
                j += 1
            blocks.append({"type": "table", "header": header, "rows": rows})
            i = j
            continue
        if not line.strip():
            flush_para(); flush_list(); i += 1; continue
        mh = _H_RE.match(line)
        if mh:
            flush_para(); flush_list()
            blocks.append({"type": "heading", "level": min(len(mh.group(1)), 3),
                           "runs": inline(mh.group(2))})
            i += 1; continue
        if line.startswith("> "):
            flush_para(); flush_list()
            blocks.append({"type": "quote", "runs": inline(line[2:])})
            i += 1; continue
        mu = _UL_RE.match(line)
        if mu:
            flush_para()
            if not cur_list or cur_list[0] != "ulist":
                flush_list(); cur_list = ("ulist", [])
            cur_list[1].append(inline(mu.group(1)))
            i += 1; continue
        mo = _OL_RE.match(line)
        if mo:
            flush_para()
            if not cur_list or cur_list[0] != "olist":
                flush_list(); cur_list = ("olist", [])
            cur_list[1].append(inline(mo.group(1)))
            i += 1; continue
        # paragraph buffer (soft-wrap)
        flush_list()
        buf.append(line)
        i += 1
    if in_code:                         # unterminated fence auto-closes
        blocks.append({"type": "code", "text": "\n".join(code_lines)})
    flush_para(); flush_list()
    return blocks or [{"type": "empty"}]


def pick_base_pt(total_chars: int) -> int:
    if total_chars < 500:
        return 12
    if total_chars < 1200:
        return 11
    if total_chars < 2500:
        return 10
    return 9


def resolve_screenshot(value: str, screenshots_dir: str) -> str | None:
    if not value or not screenshots_dir:
        return None
    name = os.path.basename(value)
    if "." not in name:                      # no extension -> not-found (no auto .png)
        return None
    path = os.path.join(screenshots_dir, name)
    return path if os.path.isfile(path) else None


def _has_decks(o) -> bool:
    return isinstance(o, dict) and ("spec" in o or "guide" in o)


def load_site_docs(raw) -> dict:
    """§3.3 우선순위: docs > top-level > 1겹 unwrap. 실패 시 ValueError."""
    if isinstance(raw, dict) and _has_decks(raw.get("docs")):
        return raw["docs"]
    if _has_decks(raw):
        return raw
    if isinstance(raw, dict):
        for k in ("data", "result"):
            if _has_decks(raw.get(k)):
                return raw[k]
    raise ValueError("SiteDocs not found: expected {spec,guide} or {docs:{...}} top-level")


def _new_prs() -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def _blank_slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _set_run(r, run, base_pt, font, mono_font, *, bold=False, pt=None, color=None):
    r.text = run["s"] if isinstance(run, dict) else run
    is_code = isinstance(run, dict) and run["t"] == "code"
    is_bold = bold or (isinstance(run, dict) and run["t"] == "bold")
    r.font.name = mono_font if is_code else font
    r.font.size = Pt(pt if pt else base_pt)
    r.font.bold = is_bold
    if color is not None:
        r.font.color.rgb = color


def add_title_slide(prs, doc, opts):
    slide = _blank_slide(prs)
    n = len(doc.get("slides", []))
    title = (opts["title_prefix"] + " " if opts["title_prefix"] else "") + doc.get("title", "")
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(2.6), Inches(12.333), Inches(1.4))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _set_run(p.add_run(), {"t": "text", "s": title}, 32, opts["font"], opts["mono_font"], bold=True)
    sub = slide.shapes.add_textbox(Inches(0.5), Inches(4.1), Inches(12.333), Inches(1.0))
    stf = sub.text_frame
    stf.word_wrap = True
    for i, txt in enumerate((_fmt_generated(doc.get("generatedAt", "")), f"슬라이드 {n}장")):
        para = stf.paragraphs[0] if i == 0 else stf.add_paragraph()
        para.alignment = PP_ALIGN.CENTER
        _set_run(para.add_run(), {"t": "text", "s": txt}, 14, opts["font"], opts["mono_font"], color=_GRAY)


def _fmt_generated(iso: str) -> str:
    # 'YYYY-MM-DDTHH:MM:SS+09:00' -> 'YYYY-MM-DD HH:MM' (slice the local-stamped ISO)
    if len(iso) >= 16 and iso[10] == "T":
        return iso[:10] + " " + iso[11:16]
    return iso[:10] if iso else ""
