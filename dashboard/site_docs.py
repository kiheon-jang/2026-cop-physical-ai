#!/usr/bin/env python3
"""사이트 문서화 빌더 — 페이지별 .md → docs JSON({spec,guide}).

3개 사이트(hdel·cop)에서 동일 파일로 사용. stdlib 만 사용.
스펙: docs/superpowers/specs/2026-06-22-site-docs-system-design.md
"""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

_SECTION_RE = re.compile(r"(?m)^##[ \t]*(기능명세|사용가이드)[ \t]*$")


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


def _apply_screenshot(base: dict, screenshots_dir: Path, proj: str, manifest: dict) -> dict:
    """manifest 에서 ui_hash 채우고, PNG 존재 시 screenshot 을 /static 경로로 재작성(없으면 "")."""
    base["ui_hash"] = manifest.get(base["id"], {}).get("ui_hash", "")
    fname = base.get("screenshot") or ""
    if fname and proj and (screenshots_dir / fname).is_file():
        base["screenshot"] = f"/static/{proj}/screenshots/{fname}"
    else:
        base["screenshot"] = ""
    return base


def _slide_base(meta: dict, fp: Path, prov: dict, kind: str) -> dict:
    return {
        "id": meta.get("id", fp.stem),
        "kind": kind,
        "title": meta.get("title", fp.stem),
        "category": meta.get("category", "시스템" if kind == "system" else ""),
        "order": _safe_int(meta.get("order")),
        "screenshot": meta.get("screenshot", ""),
        "updated_at": prov["updated_at"],
        "commit": prov["commit"],
        "ui_hash": "",
    }


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
            base = _apply_screenshot(_slide_base(meta, fp, git_provenance(repo_root, fp), "page"),
                                     screenshots_dir, proj, manifest)
            spec_slides.append({**base, "body_md": sections["spec"]})
            guide_slides.append({**base, "body_md": sections["guide"]})

    system_dir = content_dir / "system"
    if system_dir.is_dir():
        for fp in sorted(system_dir.glob("*.md")):
            meta, body = parse_frontmatter(fp.read_text(encoding="utf-8"))
            base = _apply_screenshot(_slide_base(meta, fp, git_provenance(repo_root, fp), "system"),
                                     screenshots_dir, proj, manifest)
            slide = {**base, "body_md": body.strip()}
            (guide_slides if meta.get("doc") == "guide" else spec_slides).append(slide)

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
            for field in ("id", "kind", "title", "category", "order",
                          "screenshot", "updated_at", "commit", "ui_hash", "body_md"):
                if field not in s:
                    problems.append(f"{key}:{s.get('id','?')} missing {field}")
            sid = s.get("id")
            if sid in seen:
                problems.append(f"{key} duplicate id: {sid}")
            seen.add(sid)
            if last is not None and s.get("order", 0) < last:
                problems.append(f"{key} not sorted at {sid}")
            last = s.get("order", 0)
    return problems
