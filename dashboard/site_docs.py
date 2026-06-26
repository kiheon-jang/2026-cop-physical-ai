#!/usr/bin/env python3
"""사이트 문서화 빌더 — 페이지별 .md → docs JSON({spec,guide}).

3개 사이트(hdel·cop)에서 동일 파일로 사용. stdlib 만 사용.
스펙: docs/superpowers/specs/2026-06-22-site-docs-system-design.md
슬라이드 재설계: docs/superpowers/specs/2026-06-26-site-docs-slide-redesign-design.md
"""
from __future__ import annotations

import json
import re
import struct
import subprocess
from datetime import datetime, timezone
from pathlib import Path

_SECTION_RE = re.compile(r"(?m)^##[ \t]*(기능명세|사용가이드)[ \t]*$")
_SLIDE_MARKER = re.compile(r'^<!--\s*slide\b([^>]*?)-->\s*$')
_MARKER_ATTR_RE = re.compile(r'(\w+)\s*=\s*"([^"]*)"')

ImageLayout = str  # "top" | "side" | "split" | "none"
_LAYOUTS = ("top", "side", "split", "none")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """선행 `---` 블록을 key: value 로 파싱. 없으면 ({}, 원문)."""
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta: dict[str, str] = {}
    for raw in parts[1].splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        meta[k.strip()] = v
    return meta, parts[2].lstrip("\n")


def split_doc_sections(body: str) -> dict:
    """본문을 `## 기능명세` / `## 사용가이드` 섹션으로 분리."""
    heads = [(m.group(1), m.start(), m.end()) for m in _SECTION_RE.finditer(body)]
    out = {"spec": "", "guide": ""}
    for i, (name, _m_start, c_start) in enumerate(heads):
        # c_start lands just after the header line; leading "\n" is removed by .strip()
        end = heads[i + 1][1] if i + 1 < len(heads) else len(body)
        section = body[c_start:end].strip()
        out["spec" if name == "기능명세" else "guide"] = section
    return out


def _parse_marker_attrs(s: str) -> dict:
    """`title="..." screenshot="..."` 형태의 마커 속성 파싱."""
    return {m.group(1): m.group(2) for m in _MARKER_ATTR_RE.finditer(s)}


def split_section_into_slides(section: str) -> list:
    """섹션을 `<!-- slide ... -->` 마커로 분할. 마커 없으면 1슬라이드(하위호환).

    마커 앞 본문(pre)은 자기 슬라이드로, 마커 뒤는 그 마커 슬라이드에 귀속.
    반환: [{"attrs": {...}, "body": "..."}].
    """
    lines = section.split("\n")
    chunks: list = []
    cur = None
    pre: list = []

    def push_pre():
        body = "\n".join(pre).strip()
        if body:
            chunks.append({"attrs": {}, "body": body})
        pre.clear()

    for line in lines:
        m = _SLIDE_MARKER.match(line)
        if m:
            if cur is not None:
                cur["body"] = cur["body"].strip()
                chunks.append(cur)
            else:
                push_pre()
            cur = {"attrs": _parse_marker_attrs(m.group(1) or ""), "body": ""}
        elif cur is not None:
            cur["body"] += ("\n" if cur["body"] else "") + line
        else:
            pre.append(line)
    if cur is not None:
        cur["body"] = cur["body"].strip()
        chunks.append(cur)
    else:
        push_pre()
    if not chunks:
        chunks.append({"attrs": {}, "body": section.strip()})
    return chunks


def read_png_size(path: Path):
    """PNG IHDR 에서 (w, h) 직독(stdlib, 의존성 0). 실패 시 None."""
    try:
        with open(path, "rb") as f:
            head = f.read(24)
        if len(head) < 24:
            return None
        if head[:4] != b"\x89PNG":
            return None
        w, h = struct.unpack(">II", head[16:24])
        return (w, h) if w > 0 and h > 0 else None
    except Exception:
        return None


def classify_layout(size) -> ImageLayout:
    """종횡비로 레이아웃 분류: r>=1.6 top / r<=0.95 side / 그외 split / 무이미지 none."""
    if not size:
        return "none"
    r = size[0] / size[1]
    if r >= 1.6:
        return "top"
    if r <= 0.95:
        return "side"
    return "split"


def git_provenance(repo_root: Path, file_path: Path) -> dict:
    """파일의 마지막 커밋 시각/해시. git 불가 시 mtime 폴백."""
    try:
        r = subprocess.run(
            ["git", "-C", str(repo_root), "log", "-1", "--format=%cI%x09%h", "--", str(file_path)],
            capture_output=True, text=True, timeout=5,
        )
        line = r.stdout.strip()
        if r.returncode == 0 and line:
            iso, _, short = line.partition("\t")
            return {"updated_at": iso, "commit": short}
    except Exception:
        pass
    try:
        ts = file_path.stat().st_mtime
        return {"updated_at": datetime.fromtimestamp(ts, timezone.utc).isoformat(), "commit": ""}
    except Exception:
        return {"updated_at": "", "commit": ""}


def _safe_int(value) -> int:
    try:
        return int(value) if value not in (None, "") else 0
    except (TypeError, ValueError):
        return 0


def _load_manifest(screenshots_dir: Path) -> dict:
    mf = screenshots_dir / "manifest.json"
    if mf.is_file():
        try:
            return json.loads(mf.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _shot_info(fname: str, screenshots_dir: Path, proj: str) -> tuple:
    """(url, layout). PNG 없으면 ("", "none"). 헤더 못 읽으면 이미지 살려 split 폴백."""
    ok = bool(fname) and bool(proj) and (screenshots_dir / fname).is_file()
    if not ok:
        return "", "none"
    lay = classify_layout(read_png_size(screenshots_dir / fname))
    return f"/static/{proj}/screenshots/{fname}", ("split" if lay == "none" else lay)


def _slide_base(meta: dict, fp: Path, prov: dict, kind: str, manifest: dict) -> dict:
    """슬라이드 공통 필드(screenshot/image_layout/body_md 제외 — 청크별로 채움)."""
    sid = meta.get("id", fp.stem)
    return {
        "id": sid,
        "kind": kind,
        "title": meta.get("title", fp.stem),
        "category": meta.get("category", "시스템" if kind == "system" else ""),
        "order": _safe_int(meta.get("order")),
        "updated_at": prov["updated_at"],
        "commit": prov["commit"],
        "ui_hash": manifest.get(sid, {}).get("ui_hash", ""),
    }


def _build_slides(base: dict, section: str, page_shot: str, allow_shot: bool,
                  screenshots_dir: Path, proj: str) -> list:
    """섹션을 슬라이드 리스트로. 빈 섹션은 슬라이드 안 만듦."""
    if not section.strip():
        return []
    chunks = split_section_into_slides(section)
    slides: list = []
    for i, c in enumerate(chunks):
        # attrs.screenshot 가 있으면(빈 문자열 포함) 그 값을, 없으면 page_shot 상속.
        fname = (c["attrs"].get("screenshot", page_shot)) if allow_shot else ""
        url, layout = _shot_info(fname, screenshots_dir, proj)
        # 마커 layout 속성은 화이트리스트 검증 — 오타는 계산된 종횡비 값으로 폴백.
        attr = c["attrs"].get("layout")
        image_layout = attr if attr in _LAYOUTS else layout
        slides.append({
            **base,
            "id": base["id"] if i == 0 else f'{base["id"]}--{i}',
            "title": c["attrs"].get("title", base["title"]),
            "order": base["order"] + i * 0.001,
            "screenshot": url,
            "image_layout": image_layout,
            "body_md": c["body"],
        })
    return slides


def build_site_docs(content_dir, repo_root, site_title: str = "", proj: str = "") -> dict:
    content_dir = Path(content_dir)
    repo_root = Path(repo_root)
    screenshots_dir = content_dir.parent / "screenshots"   # hdel/cop: dashboard/screenshots
    manifest = _load_manifest(screenshots_dir)
    spec_slides: list[dict] = []
    guide_slides: list[dict] = []

    pages_dir = content_dir / "pages"
    if pages_dir.is_dir():
        for fp in sorted(pages_dir.glob("*.md")):
            meta, body = parse_frontmatter(fp.read_text(encoding="utf-8"))
            sections = split_doc_sections(body)
            base = _slide_base(meta, fp, git_provenance(repo_root, fp), "page", manifest)
            page_shot = meta.get("screenshot", "")
            spec_slides.extend(_build_slides(base, sections["spec"], page_shot, True, screenshots_dir, proj))
            guide_slides.extend(_build_slides(base, sections["guide"], page_shot, True, screenshots_dir, proj))

    system_dir = content_dir / "system"
    if system_dir.is_dir():
        for fp in sorted(system_dir.glob("*.md")):
            meta, body = parse_frontmatter(fp.read_text(encoding="utf-8"))
            base = _slide_base(meta, fp, git_provenance(repo_root, fp), "system", manifest)
            slides = _build_slides(base, body.strip(), "", False, screenshots_dir, proj)
            dest = guide_slides if meta.get("doc") == "guide" else spec_slides
            dest.extend(slides)

    spec_slides.sort(key=lambda s: s["order"])
    guide_slides.sort(key=lambda s: s["order"])
    now = datetime.now(timezone.utc).isoformat()
    return {
        "spec": {"title": f"기능명세서 — {site_title}", "generatedAt": now, "slides": spec_slides},
        "guide": {"title": f"사용가이드 — {site_title}", "generatedAt": now, "slides": guide_slides},
    }


def validate_docs(docs: dict) -> list:
    """스키마 문제 목록 반환(빈 리스트 = 정상)."""
    problems: list[str] = []
    for key in ("spec", "guide"):
        doc = docs.get(key)
        if not isinstance(doc, dict) or "slides" not in doc:
            problems.append(f"missing or invalid doc: {key}")
            continue
        seen, last = set(), None
        for s in doc["slides"]:
            for field in ("id", "kind", "title", "category", "order", "screenshot",
                          "updated_at", "commit", "ui_hash", "image_layout", "body_md"):
                if field not in s:
                    problems.append(f"{key}:{s.get('id','?')} missing {field}")
            if s.get("image_layout") not in _LAYOUTS:
                problems.append(f"{key}:{s.get('id')} bad image_layout: {s.get('image_layout')}")
            cap = 1100 if s.get("image_layout") == "none" else 700
            if len(s.get("body_md", "")) > cap:
                problems.append(f"{key}:{s.get('id')} body too long ({len(s.get('body_md',''))}>{cap})")
            sid = s.get("id")
            if sid in seen:
                problems.append(f"{key} duplicate id: {sid}")
            seen.add(sid)
            if last is not None and s.get("order", 0) < last:
                problems.append(f"{key} not sorted at {sid}")
            last = s.get("order", 0)
    return problems
