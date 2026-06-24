"""site-docs PPTX/PDF 생성기 — SiteDocs JSON → .pptx (+soffice PDF).

spec: docs/superpowers/specs/2026-06-24-site-docs-pptx-export-design.md
3 repo byte-identical: cop/hdel dashboard/, hermes scripts/.
"""
from __future__ import annotations

import re

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
