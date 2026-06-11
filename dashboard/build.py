#!/usr/bin/env python3
"""CoP Physical AI Dashboard — Phase 1 MVP builder.

저장소 스캔 → JSON 인라인 → dashboard.html.
Hdel `hdelMobileResearch/dashboard/build.py` 와 동일 패턴, CoP 데이터 모델로 교체.

사용법:
    python3 dashboard/build.py                # 실데이터로 빌드
    python3 dashboard/build.py --open         # 빌드 후 브라우저로 열기
    python3 dashboard/build.py --out FILE     # 출력 경로 지정
    python3 dashboard/build.py --json-only    # HTML 생략, data.json 만 출력
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import webbrowser
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = REPO_ROOT / "dashboard"
TEMPLATE_PATH = DASHBOARD_DIR / "template.html"
DEFAULT_OUT = DASHBOARD_DIR / "dashboard.html"
DEFAULT_JSON_OUT = DASHBOARD_DIR / "data.json"
DATA_MARKER = "/*__DATA__*/"

KST = timezone(timedelta(hours=9))

# Phase 메타 — 기술 라벨(name) + 비즈니스 라벨(business_label) + outcome(이게 완료되면)
# + report_label(보고서 매핑). PHASE_ROADMAP.md 의 보고용 트랙 매핑 표를 코드로 반영.
# 4월 (Kick-off / 사전학습) 은 phase 외부. 5월부터 본격 phase 진행.
PREP_PERIOD = {
    "month": "2026-04", "weeks": 4,
    "label": "사전학습 / Kick-off",
    "outcome": "CoP 발족, 하드웨어 발주, 모방학습 핵심 자료 학습 (ACT, Diffusion Policy).",
}

PHASE_META: list[dict] = [
    {
        "id": "phase0", "name": "Phase 0 — 시뮬 환경 셋업", "month": "2026-05", "weeks": 4,
        "business_label": "5월: 실기 없이 학습할 수 있는 환경 구축",
        "outcome": "실기 로봇 없이도 학습 데이터 합성 가능. 1주일 200 에피소드 자동 생성으로 ACT 학습 사전 검증.",
        "report_label": "하드웨어 조립, 환경 구축",
    },
    {
        "id": "phase1", "name": "Phase 1 — 사전학습", "month": "2026-06", "weeks": 4,
        "business_label": "6월: AI 모델 사전학습",
        "outcome": "시뮬 환경에서 모방학습(ACT) 모델 1차 학습. 실기 적용 전 알고리즘 안정성 검증.",
        "report_label": "텔레오퍼레이션 검증",
    },
    {
        "id": "phase2", "name": "Phase 2 — Sim2Real 검증", "month": "2026-07", "weeks": 4,
        "business_label": "7월: 실기 검증 (시뮬↔실기)",
        "outcome": "시뮬 학습 모델이 실제 로봇팔에서도 작동하는지 측정. 실기 50 에피소드 수집.",
        "report_label": "데이터 50 에피소드",
    },
    {
        "id": "phase3", "name": "Phase 3 — PCB 조정", "month": "2026-08", "weeks": 4,
        "business_label": "8월: PCB 부품 픽앤플레이스",
        "outcome": "실제 PCB 부품 픽앤플레이스 학습. 정비현장 자동화 가능성 입증.",
        "report_label": "ACT 학습",
    },
    {
        "id": "phase4", "name": "Phase 4 — RS232 결선 / 1차 기능 완성", "month": "2026-09", "weeks": 4,
        "business_label": "9월: RS232 통신 학습 + 작업 완료",
        "outcome": "RS232 직렬통신 결선 자동화 + DP 비교. PCB 70% / RS232 40% 달성, 10월 시연 준비.",
        "report_label": "DP 비교, 기능 완성",
    },
]

# 프로젝트 비전 — 대시보드 히어로에 표시
PROJECT_VISION = {
    "title": "CoP Physical AI",
    "subtitle": "Physical AI (Embodied AI 기술 내재화) 를 목표로 한 SO-ARM101 기반 모방학습·강화학습 로보틱스 기술 내재화 활동",
    "subtitle_secondary": "로컬 Mac Mini 가 24시간 가동되며 Hermes Agent 가 cron 4건 (시뮬 환경 구축 · 테스트 · 일일 보고 · 주간 정리) 을 수동 개입 없이 자율 운영",
    "demo_date": "2026-10-31",
    "completion_date": "2026-09-30",  # 작업 완료 기준 (D-day 표시)
    "start_date": "2026-04-01",
    "phase_start_date": "2026-05-01",  # phase 진척률 분모 시작 (4월 = 사전학습 외부)
    "targets": [
        {
            "label": "PCB 픽앤플레이스",
            "metric": "성공률",
            "target": "70%",
            "context": "Phase 3 (8월) 평가 · 정비현장 자동화 가능성 입증",
            "icon": "wrench",
        },
        {
            "label": "RS232 HHT 결선",
            "metric": "부분 성공률",
            "target": "40%",
            "context": "Phase 4 (9월) 평가 · 정밀 삽입 (±0.5mm)",
            "icon": "plug",
        },
    ],
}

# Obsidian 월별 활동보고서 위치
OBSIDIAN_REPORT_DIR = Path.home() / "Documents" / "second-brain" / "03 Areas" / "회사문서" / "CoP_PhysicalAI"

# 카테고리 자동 추론 — 본문 키워드 매칭 (대소문자 무시).
CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("MuJoCo/MJCF",     ["mujoco", "mjcf", "freejoint", "geom", "viewer"]),
    ("Camera",          ["camera", "renderer", "rgb", "오버헤드", "그리퍼 카메라"]),
    ("Kinematics",      ["joint", "관절", "kinematics", "calibration", "캘리브"]),
    ("Pick-Place",      ["pick", "place", "pick-place", "grasp", "큐브"]),
    ("Data Collection", ["dataset", "에피소드", "data_collector", "lerobot dataset"]),
    ("ACT",             ["act ", "imitation", "모방학습", "policy"]),
    ("DP",              ["diffusion policy", " dp "]),
    ("Sim2Real",        ["sim2real", "sim-to-real", "domain randomization"]),
    ("Hardware",        ["pcb", "rs232", "serial", " hht", "결선"]),
]


# ─────────────────────────────────────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def make_id(*parts: str) -> str:
    h = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()
    return h[:10]


def read_text(p: Path, limit: int | None = None) -> str:
    try:
        s = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    return s[:limit] if limit else s


def infer_category(text: str) -> str:
    low = text.lower()
    hit: list[str] = []
    for cat, keywords in CATEGORY_RULES:
        if any(k in low for k in keywords):
            hit.append(cat)
            if len(hit) >= 2:
                break
    return " · ".join(hit) if hit else "General"


_DATE_FROM_FILENAME = re.compile(r"(20\d{2})[-_](\d{1,2})[-_](\d{1,2})")


def parse_date_from_filename(name: str) -> str | None:
    """파일명에서 YYYY-MM-DD 추출. 'YYYY-MM-DD_step.md', '2026-06-06.md' 등."""
    m = _DATE_FROM_FILENAME.search(name)
    if not m:
        return None
    y, mo, d = m.groups()
    try:
        return datetime(int(y), int(mo), int(d)).strftime("%Y-%m-%d")
    except ValueError:
        return None


def first_h1(text: str) -> str:
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("# "):
            # 후행 — YYYY-MM-DD (요일) 부분은 떼어냄
            title = re.sub(r"\s*—\s*\d{4}-\d{2}-\d{2}.*$", "", s.lstrip("# ").strip())
            return title.strip()
    return ""


def extract_section(text: str, heading: str) -> str:
    """## 헤딩 안의 본문 (다음 헤딩 전까지) 반환."""
    pattern = re.compile(
        r"^##\s+" + re.escape(heading) + r"\s*$(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


def excerpt(text: str, limit: int = 200) -> str:
    """첫 비어있지 않은 줄 (제목 제외) 의 발췌."""
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith(">") or s.startswith("---"):
            continue
        return s[:limit] + ("…" if len(s) > limit else "")
    return ""


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 15) -> str:
    try:
        r = subprocess.run(
            cmd, cwd=str(cwd) if cwd else None,
            capture_output=True, text=True, timeout=timeout,
        )
        return r.stdout if r.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# PHASE_ROADMAP 파서 (메뉴 1, 5)
# ─────────────────────────────────────────────────────────────────────────────

_PHASE_HEADING = re.compile(r"^##\s+Phase\s+(\d+)\s+—\s+(.+?)\s*\((.+?)\)\s*$", re.MULTILINE)
_WEEK_HEADING = re.compile(r"^###\s+W(\d+(?:-\d+)?)\s*(?:\((.+?)\))?\s*(?:—\s+(.+?))?\s*$", re.MULTILINE)
_CHECK_ITEM = re.compile(r"^\s*-\s*\[(v| )\]\s+(?:\*\*(.+?)\*\*\s*:\s*)?(.+?)\s*$", re.MULTILINE)


def build_phase_roadmap() -> tuple[list[dict], str]:
    """Returns (phases, current_phase_label)."""
    roadmap = REPO_ROOT / "research" / "simulation" / "PHASE_ROADMAP.md"
    text = read_text(roadmap)
    if not text:
        return [], "(PHASE_ROADMAP.md not found)"

    # Phase 단위 split
    phase_starts = [(m.start(), m.group(1), m.group(2), m.group(3)) for m in _PHASE_HEADING.finditer(text)]
    phase_starts.append((len(text), "_END_", "", ""))

    # 사전학습 (4월, phase 외부) — Gantt 표시 + KPI 평균에선 제외
    phases: list[dict] = [{
        "id": "prep",
        "name": "사전학습 / Kick-off",
        "date_range": "2026.04.01 ~ 2026.04.30",
        "month": PREP_PERIOD["month"],
        "weeks": [],
        "progress": 1.0,
        "done": 0, "total": 0,
        "status": "완료",
        "business_label": "4월: Kick-off, 하드웨어 발주",
        "outcome": PREP_PERIOD["outcome"],
        "report_label": "Kick-off, 하드웨어 발주",
        "is_prep": True,
    }]
    current_label = "(no active phase)"
    for i, (start, num, name, date_range) in enumerate(phase_starts[:-1]):
        end = phase_starts[i + 1][0]
        body = text[start:end]
        meta = next((p for p in PHASE_META if p["id"] == f"phase{num}"), None)

        weeks: list[dict] = []
        week_starts = [(m.start(), m.groups()) for m in _WEEK_HEADING.finditer(body)]
        week_starts.append((len(body), None))
        for j, (ws, wgroups) in enumerate(week_starts[:-1]):
            if wgroups is None:
                continue
            wnum, wrange, wname = wgroups
            we = week_starts[j + 1][0]
            wbody = body[ws:we]
            items = []
            for cm in _CHECK_ITEM.finditer(wbody):
                checked = cm.group(1) == "v"
                date_label = cm.group(2) or ""
                task = cm.group(3).strip()
                items.append({"checked": checked, "date": date_label, "task": task[:200]})
            total = len(items)
            done = sum(1 for it in items if it["checked"])
            weeks.append({
                "week": f"W{wnum}",
                "name": (wname or "").strip(),
                "date_range": (wrange or "").strip(),
                "items": items,
                "progress": (done / total) if total else 0.0,
                "done": done, "total": total,
            })

        all_items = [it for w in weeks for it in w["items"]]
        total_all = len(all_items)
        done_all = sum(1 for it in all_items if it["checked"])
        progress = (done_all / total_all) if total_all else 0.0
        status = "완료" if progress >= 0.999 else ("진행" if progress > 0 else "예정")

        # 첫 미완료 phase (progress < 1.0) 의 첫 미체크 항목 → current label
        if progress < 1.0 and total_all > 0 and current_label.startswith("(no"):
            for w in weeks:
                next_item = next((it for it in w["items"] if not it["checked"]), None)
                if next_item:
                    current_label = f"Phase {num} - {w['week']} - {next_item['task'][:60]}"
                    break

        phases.append({
            "id": f"phase{num}",
            "name": (meta["name"] if meta else f"Phase {num} — {name.strip()}"),
            "date_range": date_range.strip(),
            "month": meta["month"] if meta else "",
            "weeks": weeks,
            "progress": round(progress, 3),
            "done": done_all, "total": total_all,
            "status": status,
            # 비전공자용 이중 라벨 (R2)
            "business_label": meta["business_label"] if meta else "",
            "outcome": meta["outcome"] if meta else "",
            "report_label": meta["report_label"] if meta else "",
        })
    return phases, current_label


# ─────────────────────────────────────────────────────────────────────────────
# research/simulation/*.md (메뉴 2 — 시뮬 작업)
# ─────────────────────────────────────────────────────────────────────────────

def build_sim_tasks() -> list[dict]:
    sim_dir = REPO_ROOT / "research" / "simulation"
    if not sim_dir.exists():
        return []
    tasks: list[dict] = []
    for p in sim_dir.glob("*.md"):
        if p.name == "PHASE_ROADMAP.md":
            continue
        text = read_text(p, limit=20_000)
        date = parse_date_from_filename(p.name)
        title = first_h1(text) or p.stem
        phase_label = extract_section(text, "오늘 진행 단계").splitlines()[0].strip() if extract_section(text, "오늘 진행 단계") else ""
        category = infer_category(text[:3000])
        # 본문에 언급된 스크립트 추출
        scripts = sorted(set(re.findall(r"\b(sim_[a-z_]+\.py)\b", text)))
        # phase_id 추출: 1) phase_label, 2) title, 3) 본문 첫 1KB, 4) 날짜 기반 (월별 매핑)
        pm = re.search(r"Phase\s+(\d+)", phase_label) or \
             re.search(r"Phase\s+(\d+)", title) or \
             re.search(r"Phase\s+(\d+)", text[:1500])
        phase_id = ""
        if pm:
            phase_id = f"phase{pm.group(1)}"
        elif date:
            # 월별 매핑 (PHASE_META 참조): 5월=phase0, 6월=phase1, 7월=phase2, ... (4월은 phase 외부 prep)
            month = date[:7]
            for meta in PHASE_META:
                if meta["month"] == month:
                    phase_id = meta["id"]
                    break
        tasks.append({
            "id": make_id("sim", p.name),
            "title": title,
            "date": date or "",
            "phase_label": phase_label,
            "phase_id": phase_id,
            "group": phase_id,  # Hdel chip 필터 호환 (data-filter="group" data-value="phase0" 등)
            "category": category,
            "excerpt": excerpt(text),
            "path": str(p.relative_to(REPO_ROOT)),
            "scripts_mentioned": scripts,
        })
    tasks.sort(key=lambda t: t["date"] or "0", reverse=True)
    return tasks


# ─────────────────────────────────────────────────────────────────────────────
# agent/research-log/*.md (메뉴 3 — 일일 진척)
# ─────────────────────────────────────────────────────────────────────────────

_SELF_HEAL = re.compile(r"^\s*-\s*\[자가치유\]\s*(.+?)$", re.MULTILINE)
_SCRIPT_LINE = re.compile(r"^###\s+스크립트:\s*(.+?)\s*$", re.MULTILINE)


def build_daily() -> list[dict]:
    log_dir = REPO_ROOT / "agent" / "research-log"
    if not log_dir.exists():
        return []
    out: list[dict] = []
    for p in sorted(log_dir.glob("*.md"), reverse=True):
        text = read_text(p, limit=30_000)
        date = parse_date_from_filename(p.name) or p.stem
        h1 = first_h1(text)
        # weekday 추출 (예: "# 시뮬 진척 — 2026-06-06 (목요일)")
        wm = re.search(r"\(([월화수목금토일])요일?\)", text[:300])
        weekday = wm.group(1) if wm else ""
        phase_text = extract_section(text, "오늘 진행 단계").splitlines()
        phase_label = phase_text[0].strip() if phase_text else ""
        scripts = _SCRIPT_LINE.findall(text)
        self_heal = [m.strip() for m in _SELF_HEAL.findall(text)]
        next_steps = []
        ns_block = extract_section(text, "다음 단계")
        for line in ns_block.splitlines():
            s = line.strip().lstrip("-").strip()
            if s:
                next_steps.append(s[:200])
        out.append({
            "id": make_id("daily", p.name),
            "date": date,
            "weekday": weekday,
            "title": h1,
            "phase_label": phase_label,
            "scripts": scripts,
            "self_heal_actions": self_heal,
            "next_steps": next_steps[:6],
            "excerpt": excerpt(text, 240),
            "path": str(p.relative_to(REPO_ROOT)),
        })
    return out


# ─────────────────────────────────────────────────────────────────────────────
# agent/report-evidence/YYYY-MM/ (메뉴 4 — 월간 보고용 증거)
# ─────────────────────────────────────────────────────────────────────────────

def build_evidence() -> list[dict]:
    ev_dir = REPO_ROOT / "agent" / "report-evidence"
    if not ev_dir.exists():
        return []
    out: list[dict] = []
    for mdir in sorted(ev_dir.iterdir(), reverse=True):
        if not mdir.is_dir():
            continue
        index_file = mdir / "INDEX.md"
        index_text = read_text(index_file) if index_file.exists() else ""
        weekly = []
        for wfile in sorted(mdir.glob("W*_summary.md")):
            weekly.append({
                "week": wfile.stem.split("_")[0],
                "path": str(wfile.relative_to(REPO_ROOT)),
                "excerpt": excerpt(read_text(wfile, limit=3000), 200),
            })
        out.append({
            "month": mdir.name,
            "index_path": str(index_file.relative_to(REPO_ROOT)) if index_file.exists() else None,
            "index_excerpt": excerpt(index_text, 240),
            "weekly_summaries": weekly,
        })
    return out


# ─────────────────────────────────────────────────────────────────────────────
# agent/external-dependencies.md (메뉴 6 — 외부 의존 차단)
# ─────────────────────────────────────────────────────────────────────────────

_BLOCKER_ITEM = re.compile(
    r"^\s*-\s*\[(v| )\]\s*(?:\[(.+?)\])?\s*\*?\*?(.+?)\*?\*?\s*(?:\*\((.+?)\)\*)?\s*$",
    re.MULTILINE,
)
_DEADLINE = re.compile(r"마감(?:일)?\s*:?\s*(20\d{2}-\d{2}-\d{2})")


def build_blockers() -> list[dict]:
    blockers_file = REPO_ROOT / "agent" / "external-dependencies.md"
    text = read_text(blockers_file)
    if not text:
        return []
    out: list[dict] = []
    # 단순화: 각 - [ ] 또는 - [v] 라인을 잡고, 다음 빈 줄까지의 컨텍스트를 'detail' 로
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = _BLOCKER_ITEM.match(lines[i])
        if not m:
            i += 1
            continue
        checked = m.group(1) == "v"
        owner = (m.group(2) or "").strip() or "(미지정)"
        title = m.group(3).strip().strip("*").strip()
        note = (m.group(4) or "").strip()
        # 다음 라인부터 들여쓰기로 시작하는 줄들 = 상세
        detail_lines: list[str] = []
        j = i + 1
        while j < len(lines):
            if not lines[j].strip():
                break
            if not lines[j].startswith((" ", "\t", "  -")):
                if lines[j].lstrip().startswith("-"):
                    # 새 항목 시작
                    if _BLOCKER_ITEM.match(lines[j]):
                        break
                else:
                    break
            detail_lines.append(lines[j].strip().lstrip("-").strip())
            j += 1
        detail_text = "\n".join(detail_lines)
        dl = _DEADLINE.search(detail_text + " " + note)
        deadline = dl.group(1) if dl else ""
        # 우선순위 추론: 최근 ## 헤딩에서 "우선순위 1/2" 단어로 추정
        # 단순화: title 의 위치를 보고 결정. 일단 default 2.
        priority = 1 if "우선순위 1" in text[:text.find(lines[i])] else 2
        out.append({
            "id": make_id("blocker", title),
            "checked": checked,
            "owner": owner,
            "title": title[:200],
            "note": note[:200],
            "deadline": deadline,
            "detail": detail_text[:600],
            "priority": priority,
        })
        i = j
    return out


# ─────────────────────────────────────────────────────────────────────────────
# samples/SAMPLE_STATUS.md (메뉴 7 — 샘플 코드 상태)
# ─────────────────────────────────────────────────────────────────────────────

_STATUS_EMOJI_MAP = {
    "✅": ("complete", 4),
    "🟢": ("basic", 2),
    "🟡": ("wip", 1),
    "📋": ("planned", 0),
}
_TABLE_ROW = re.compile(
    r"^\|\s*`?([^`|]+?)`?\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$",
    re.MULTILINE,
)
_CATEGORY_HEADING = re.compile(r"^##\s+([\w./-]+)/\s*—\s*(.+?)\s*$", re.MULTILINE)


def build_samples() -> dict:
    status_file = REPO_ROOT / "samples" / "SAMPLE_STATUS.md"
    text = read_text(status_file)
    if not text:
        return {"summary": {}, "files": []}

    files: list[dict] = []
    current_category = ""
    for line in text.splitlines():
        ch = _CATEGORY_HEADING.match(line)
        if ch:
            current_category = ch.group(1).strip()
            continue
        rm = _TABLE_ROW.match(line)
        if not rm or not current_category:
            continue
        path, status_raw, completion, last_verified, desc = (g.strip() for g in rm.groups())
        if path.lower() == "파일" or "---" in path or "상태" in status_raw:
            continue
        # status emoji 매칭
        status_key, stars = "unknown", 0
        for emoji, (key, s) in _STATUS_EMOJI_MAP.items():
            if emoji in status_raw:
                status_key, stars = key, s
                break
        files.append({
            "path": f"{current_category}/{path}" if not path.startswith(current_category) else path,
            "category": current_category,
            "status": status_key,
            "status_label": status_raw,
            "completion": completion,
            "stars": stars,
            "last_verified": last_verified,
            "description": desc[:200],
        })

    # 카테고리별 요약 (complete / basic / wip / planned)
    summary: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])
    for f in files:
        idx = {"complete": 0, "basic": 1, "wip": 2, "planned": 3}.get(f["status"], 3)
        summary[f["category"]][idx] += 1

    return {"summary": dict(summary), "files": files}


# ─────────────────────────────────────────────────────────────────────────────
# research/decisions/*.md (메뉴 8 — 결정)
# ─────────────────────────────────────────────────────────────────────────────

def build_decisions() -> list[dict]:
    dec_dir = REPO_ROOT / "research" / "decisions"
    if not dec_dir.exists():
        return []
    out: list[dict] = []
    for p in sorted(dec_dir.glob("*.md"), reverse=True):
        if p.name == "README.md":
            continue
        text = read_text(p, limit=10_000)
        date = parse_date_from_filename(p.name) or ""
        out.append({
            "id": make_id("decision", p.name),
            "title": first_h1(text) or p.stem,
            "date": date,
            "excerpt": excerpt(text, 280),
            "path": str(p.relative_to(REPO_ROOT)),
        })
    return out


# ─────────────────────────────────────────────────────────────────────────────
# 통계 (메뉴 12 — 분석)
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# R2: 비즈니스 KPI / 월별 보고서 / 영상 / 활동 타임라인
# ─────────────────────────────────────────────────────────────────────────────

def build_business_kpi(phases: list[dict]) -> dict:
    """프로젝트 비전 + D-day + 목표 달성률 + 위험 신호.

    관리자 보고용 — 한 화면에 "어디까지 왔고 어디로 가는가" 표시.
    """
    today = datetime.now(KST).date()
    try:
        demo = datetime.strptime(PROJECT_VISION["demo_date"], "%Y-%m-%d").date()
        start = datetime.strptime(PROJECT_VISION["start_date"], "%Y-%m-%d").date()
        completion = datetime.strptime(PROJECT_VISION["completion_date"], "%Y-%m-%d").date()
        phase_start = datetime.strptime(PROJECT_VISION["phase_start_date"], "%Y-%m-%d").date()
    except (ValueError, KeyError):
        demo = today; start = today; completion = today; phase_start = today
    # D-day: 기능 완성 기준 (9/30)
    d_day = (completion - today).days
    d_day_demo = (demo - today).days
    # 시간 경과: phase 시작 (5/1) ~ 완료 (9/30) 기준. 4월은 사전학습이라 별도.
    phase_span = max((completion - phase_start).days, 1)
    phase_elapsed_days = max(0, (today - phase_start).days)
    time_elapsed = min(phase_elapsed_days / phase_span, 1.0)
    elapsed_days = max(0, (today - start).days)  # 사업 착수일 기준 (참고용)

    # 목표 달성률: phase 별 progress 의 단순 평균 (사전학습 prep 제외, 5개 phase 균등 가중).
    # 분모: phase_start(5/1) ~ completion(9/30) 구간이라 prep(4월) 은 elapsed 와 phase 평균 양쪽 모두 제외 → 일관.
    phase_progresses = [p.get("progress", 0.0) for p in phases if not p.get("is_prep")]
    target_progress = (sum(phase_progresses) / len(phase_progresses)) if phase_progresses else 0.0

    # 현재 진행 중 phase + 다음 미완료 항목 3개
    current = next((p for p in phases if p.get("status") == "진행"), None)
    next_actions: list[str] = []
    if current:
        for w in current.get("weeks", []):
            for it in w.get("items", []):
                if not it.get("checked"):
                    next_actions.append(it.get("task", "")[:120])
                    if len(next_actions) >= 3:
                        break
            if len(next_actions) >= 3:
                break

    return {
        **PROJECT_VISION,
        "d_day": d_day,
        "d_day_demo": d_day_demo,
        "elapsed_days": elapsed_days,
        "phase_elapsed_days": phase_elapsed_days,
        "time_elapsed": round(time_elapsed, 3),
        "target_progress": round(target_progress, 3),
        "current_phase_id": current.get("id") if current else "",
        "current_phase_label": current.get("name") if current else "",
        "current_phase_business": current.get("business_label") if current else "",
        "next_actions": next_actions,
        # 진척 vs 일정 비교: 시간 X% 지났는데 목표 Y% 달성 → 격차 표시
        "progress_vs_time_gap": round(target_progress - time_elapsed, 3),
    }


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """YAML frontmatter 파서 — PyYAML 사용 (3rd-party 의존성 1개 추가).

    형식:
      ---
      <yaml content>
      ---
      <body>

    반환: (frontmatter_dict, body_without_frontmatter)
    프론트매터 없으면 ({}, text). 파싱 실패 시 raw text 그대로 반환.
    """
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text
    raw = text[4:end]
    body = text[end + 4:].lstrip("\n")
    try:
        import yaml
        from datetime import date, datetime as _dt
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            return {}, body
        # date/datetime → ISO string (JSON 직렬화 안전화)
        def _norm(v):
            if isinstance(v, (date, _dt)):
                return v.isoformat()
            if isinstance(v, dict):
                return {k: _norm(vv) for k, vv in v.items()}
            if isinstance(v, list):
                return [_norm(x) for x in v]
            return v
        return _norm(data), body
    except Exception:
        return {}, body


def build_monthly_reports() -> list[dict]:
    """Obsidian 03 Areas/회사문서/CoP_PhysicalAI/CoP_*_활동보고서.md 풀 임베드.

    같은 month 에 여러 파일 (예: 4월 v1 + v20260427) 있으면 mtime 최신 1건만 노출.

    FORM-1: YAML frontmatter 있으면 form 필드로 emit (대시보드 폼 양식 렌더용).
    frontmatter 없으면 form=None, 기존 body_md 만 노출 (마크다운 fallback).
    """
    if not OBSIDIAN_REPORT_DIR.exists():
        return []
    # month → (mtime, path) 매핑으로 최신만 선택
    latest_by_month: dict[str, Path] = {}
    for f in OBSIDIAN_REPORT_DIR.glob("CoP_PhysicalAI_*_활동보고서*.md"):
        m = re.search(r"(\d{4}-\d{2})", f.name)
        month = m.group(1) if m else f.stem
        cur = latest_by_month.get(month)
        if cur is None or f.stat().st_mtime > cur.stat().st_mtime:
            latest_by_month[month] = f
    out: list[dict] = []
    for month in sorted(latest_by_month.keys()):
        f = latest_by_month[month]
        text = read_text(f, limit=40_000)
        if not text:
            continue
        form, body = _parse_frontmatter(text)
        out.append({
            "id": make_id("report", f.name),
            "month": month,
            "title": first_h1(body or text) or f.stem,
            "filename": f.name,
            "excerpt": excerpt(body or text, 400),
            "body_md": body or text,  # frontmatter 제외한 본문 (없으면 전체)
            "form": form if form else None,  # FORM-1: 폼 양식 데이터
            "path": str(f),
            "size_bytes": len(text),
        })
    return out


# 비전공자용 영상 설명 — 파일명 키워드 기반.
# 모든 영상은 학습 전 단계 시뮬 (휴리스틱/IK 기반). ACT 학습 결과 X.
_VIDEO_DESCRIPTIONS = [
    (("6dof", "6-dof"),     "6축 로봇팔 기본 움직임 — 시뮬 환경 동작 검증"),
    (("pick_place", "pick-place", "pickplace"),  "픽앤플레이스 시나리오 시뮬 — 데이터 수집용 (학습 전, IK 기반. 큐브 실패가 정상)"),
    (("camera",),           "시뮬 환경 내 카메라 동작 검증"),
    (("headless",),         "헤드리스 모드 비디오 (UI 없이 백그라운드 렌더)"),
    (("data_collect", "data-collect"),  "학습용 데이터 수집 — 한 에피소드 기록"),
    (("teleop",),           "텔레오퍼레이션 — 사람이 조종하는 로봇팔 시연"),
    (("연결", "connect"),   "하드웨어 연결 검증"),
]


def _describe_video(filename: str) -> str:
    n = filename.lower()
    for keys, desc in _VIDEO_DESCRIPTIONS:
        if any(k in n for k in keys):
            return desc
    return "시뮬레이션 결과 영상"


def build_videos() -> list[dict]:
    """모든 시각 자산 통합 — 학습 데이터셋 영상 (hero) + 시뮬 영상 + frame 시퀀스.

    노출 순서:
      1) data/episodes/videos/.../file-000.mp4 — 200 ep 학습 데이터셋 (가장 강력한 진행 증거)
      2) research/simulation/video/*.mp4 — pick_place / 6dof 시나리오 시뮬
      3) overhead_frame_sequence (30장)
      4) gripper_frame_sequence (30장)
    """
    video_dir = REPO_ROOT / "research" / "simulation" / "video"
    out: list[dict] = []

    # 첫 키 프레임 (있다면 모든 영상의 poster 로 공통 사용)
    first_frame = next(iter(sorted(video_dir.glob("overhead_frame_0000.png"))), None) if video_dir.exists() else None
    poster_default = str(first_frame.relative_to(REPO_ROOT)) if first_frame else None

    # 1) 학습 데이터셋 영상 — 200 에피소드 합성 결과 (있으면 가장 먼저 노출)
    dataset_video = REPO_ROOT / "data" / "episodes" / "videos" / "observation.images.top" / "chunk-000" / "file-000.mp4"
    if dataset_video.exists():
        try:
            st = dataset_video.stat()
            ep_count, frame_count = 200, 12400
            info_json = REPO_ROOT / "data" / "episodes" / "meta" / "info.json"
            if info_json.exists():
                try:
                    info = json.loads(info_json.read_text())
                    ep_count = info.get("total_episodes", ep_count)
                    frame_count = info.get("total_frames", frame_count)
                except Exception:
                    pass
            out.append({
                "id": make_id("video", "dataset_top"),
                "filename": "dataset_top_camera.mp4",
                "path": str(dataset_video.relative_to(REPO_ROOT)),
                "kind": "dataset",
                "size_bytes": st.st_size,
                "modified": datetime.fromtimestamp(st.st_mtime, KST).isoformat(timespec="seconds"),
                "poster": poster_default,
                "description": f"학습 데이터셋 영상 — {ep_count} 에피소드 / {frame_count:,} 프레임 (천장 카메라 시점, ACT 학습 직전 단계 산출물)",
                "preload": "none",  # 27MB — 클릭 시 로드
                "episode_count": ep_count,
                "frame_count_total": frame_count,
            })
        except OSError:
            pass

    # 2) 시뮬 영상 (research/simulation/video)
    if video_dir.exists():
        for mp4 in sorted(video_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                st = mp4.stat()
            except OSError:
                continue
            out.append({
                "id": make_id("video", mp4.name),
                "filename": mp4.name,
                "path": str(mp4.relative_to(REPO_ROOT)),
                "kind": ("pick-place" if "pick" in mp4.name.lower()
                         else "6dof" if "6dof" in mp4.name.lower()
                         else "sim"),
                "size_bytes": st.st_size,
                "modified": datetime.fromtimestamp(st.st_mtime, KST).isoformat(timespec="seconds"),
                "poster": poster_default,
                "description": _describe_video(mp4.name),  # 비전공자용 한 줄
                "preload": "metadata",
            })

        # 3) 오버헤드 프레임 carousel
        overhead_frames = sorted(video_dir.glob("overhead_frame_*.png"))
        if overhead_frames:
            out.append({
                "id": make_id("frames", "overhead"),
                "filename": "overhead_frame_sequence",
                "path": str(video_dir.relative_to(REPO_ROOT)),
                "kind": "frame-sequence",
                "size_bytes": sum(p.stat().st_size for p in overhead_frames),
                "frame_count": len(overhead_frames),
                "frames": [str(p.relative_to(REPO_ROOT)) for p in overhead_frames[:30]],
                "description": "천장 카메라 시점 — 30장 프레임 시퀀스 (시뮬 동작 결과)",
            })

        # 4) 그리퍼 프레임 carousel (그리퍼 손목 카메라 시점)
        gripper_frames = sorted(video_dir.glob("gripper_frame_*.png"))
        if gripper_frames:
            out.append({
                "id": make_id("frames", "gripper"),
                "filename": "gripper_frame_sequence",
                "path": str(video_dir.relative_to(REPO_ROOT)),
                "kind": "frame-sequence",
                "size_bytes": sum(p.stat().st_size for p in gripper_frames),
                "frame_count": len(gripper_frames),
                "frames": [str(p.relative_to(REPO_ROOT)) for p in gripper_frames[:30]],
                "description": "그리퍼 손목 카메라 시점 — 30장 (학습 입력의 두 번째 카메라 시점)",
            })

    return out


def build_training_metrics() -> dict:
    """ACT 학습 메트릭 reader (PROG-2).

    학습이 진행되면 outputs/train/*/metrics.jsonl 에서 epoch/loss/step 읽어 차트용 emit.
    학습 미시작 시 status="pending" 반환 → 대시보드에서 "학습 시작 대기" 노출.

    metrics.jsonl 한 줄당 JSON (train_act.py 가 epoch 끝마다 append):
      {"epoch": int, "step": int, "loss": float, "lr": float,
       "timestamp": str, "val_loss": float?, "success_rate": float?}
    """
    metrics_files = list(REPO_ROOT.glob("outputs/train/*/metrics.jsonl"))
    if not metrics_files:
        return {
            "status": "pending",
            "message": "ACT 학습 시작 대기 중 (2026-06-15 Phase 1 W3 예정)",
            "epochs": [],
            "current_epoch": 0,
        }
    # 가장 최근 메트릭 파일
    latest = max(metrics_files, key=lambda p: p.stat().st_mtime)
    epochs: list[dict] = []
    try:
        with open(latest) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    epochs.append(json.loads(line))
                except Exception:
                    pass
    except OSError:
        return {
            "status": "pending",
            "message": "메트릭 파일 읽기 실패",
            "epochs": [],
            "current_epoch": 0,
        }
    if not epochs:
        return {
            "status": "pending",
            "message": "메트릭 파일은 있으나 데이터 없음",
            "epochs": [],
            "current_epoch": 0,
        }
    # 24h 안에 새 epoch 추가됐으면 running, 아니면 paused
    try:
        last_ts = epochs[-1].get("timestamp", "")
        last_dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
        idle_sec = (datetime.now(KST) - last_dt.astimezone(KST)).total_seconds()
        status = "running" if idle_sec < 86400 else "paused"
    except Exception:
        status = "running"
    losses = [e["loss"] for e in epochs if isinstance(e.get("loss"), (int, float))]
    return {
        "status": status,
        "epochs": epochs,
        "current_epoch": epochs[-1].get("epoch", 0),
        "current_step": epochs[-1].get("step", 0),
        "current_loss": epochs[-1].get("loss"),
        "best_loss": min(losses) if losses else None,
        "current_lr": epochs[-1].get("lr"),
        "job_name": latest.parent.name,
        "metrics_path": str(latest.relative_to(REPO_ROOT)),
    }


def build_inference_progress() -> list[dict]:
    """ACT 학습 진척 inference 영상 scan (PROG-2).

    `research/simulation/inference_progress/*.mp4` → 시간순 list.
    파일명 패턴 (cron 페이로드에서 생성): `inference_epoch_{NN}_{date}.mp4`
    """
    progress_dir = REPO_ROOT / "research" / "simulation" / "inference_progress"
    if not progress_dir.exists():
        return []
    out: list[dict] = []
    for mp4 in sorted(progress_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime):
        try:
            st = mp4.stat()
        except OSError:
            continue
        m = re.search(r"epoch[_-]?(\d+)", mp4.stem.lower())
        epoch = int(m.group(1)) if m else None
        out.append({
            "id": make_id("inference", mp4.name),
            "filename": mp4.name,
            "path": str(mp4.relative_to(REPO_ROOT)),
            "epoch": epoch,
            "size_bytes": st.st_size,
            "modified": datetime.fromtimestamp(st.st_mtime, KST).isoformat(timespec="seconds"),
        })
    return out


def build_hardware_photos() -> list[dict]:
    """models/SO-ARM100/media/ 에서 핵심 하드웨어 사진 노출.
    관리자 보고용 — "실제 진행 중인 하드웨어 시각자료"."""
    media_dir = REPO_ROOT / "models" / "SO-ARM100" / "media"
    if not media_dir.exists():
        return []
    # 핵심 사진만 큐레이션 (파일명 → 한국어 설명)
    curation = [
        ("Leader_And_Follower_SO100.jpg", "Leader + Follower 로봇팔 (텔레오퍼레이션 페어)"),
        ("SO101_Leader.webp",            "SO-ARM101 Leader (조작 측)"),
        ("SO101_Follower.webp",          "SO-ARM101 Follower (작업 측)"),
        ("d405_mount_sample_observation.jpg", "RealSense D405 카메라 마운트 (그리퍼 시점 학습 입력)"),
    ]
    out: list[dict] = []
    for fname, desc in curation:
        f = media_dir / fname
        if not f.exists():
            continue
        try:
            st = f.stat()
        except OSError:
            continue
        out.append({
            "id": make_id("hw", fname),
            "filename": fname,
            "path": str(f.relative_to(REPO_ROOT)),
            "size_bytes": st.st_size,
            "description": desc,
        })
    return out


def build_activity_timeline(daily: list[dict], sim_tasks: list[dict], days: int = 60) -> list[dict]:
    """git log + research-log + sim_tasks 를 날짜별로 묶음.

    "활동 타임라인" — CoP 학습 본질 활동만 (시뮬/로그/히스토리/데이터/학습/테스트).
    [대시보드]/[보고가드] 등 도구 작업은 제외. self-heal 커밋은 별도 카운트.
    """
    # CoP 학습 본질 카테고리만 통과시키는 화이트리스트.
    # commit 메시지의 [태그] 가 이 prefix 중 하나로 시작해야 활동 타임라인에 포함.
    CORE_ACTIVITY_TAGS = (
        "시뮬", "로그", "히스토리", "주간정리", "데이터", "학습", "테스트",
        "보고서", "결정", "메일",
    )
    today = datetime.now(KST).date()
    cutoff = today - timedelta(days=days)
    log_out = run(
        ["git", "log", f"--since={cutoff.isoformat()}",
         "--pretty=format:%ad|%s|%h", "--date=short"],
        cwd=REPO_ROOT, timeout=15,
    )
    by_date: dict[str, dict] = {}
    for line in log_out.splitlines():
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue
        date, msg, sha = parts
        bucket = by_date.setdefault(date, {
            "commits": [], "self_heal_count": 0,
            "categories": set(),
        })
        if "self-heal" in msg.lower() or "자가치유" in msg:
            bucket["self_heal_count"] += 1
            continue
        # 카테고리 추출 — 메시지의 [태그] 패턴
        cm = re.search(r"\[([^\]]+)\]", msg)
        tag = cm.group(1).strip() if cm else ""
        # 화이트리스트: 학습 본질 태그가 아니면 commit 자체를 활동 타임라인에서 제외.
        # 단, daily/sim_tasks 매칭은 그대로 살리기 위해 bucket 자체는 보존.
        if not tag or not any(tag.startswith(p) for p in CORE_ACTIVITY_TAGS):
            continue
        bucket["commits"].append({"msg": msg[:120], "sha": sha})
        bucket["categories"].add(tag)

    daily_by_date = {d["date"]: d for d in daily if d.get("date")}
    sim_by_date: dict[str, list[dict]] = {}
    for t in sim_tasks:
        if t.get("date"):
            sim_by_date.setdefault(t["date"], []).append(t)

    # 학습 본질 활동이 0건인 날은 타임라인에서 제외. sim_task 만 있거나 self-heal 만 있는 날은 유지.
    all_dates = set(by_date.keys()) | set(daily_by_date.keys()) | set(sim_by_date.keys())
    timeline: list[dict] = []
    for date in sorted(all_dates, reverse=True):
        info = by_date.get(date, {"commits": [], "self_heal_count": 0, "categories": set()})
        d = daily_by_date.get(date, {})
        sims = sim_by_date.get(date, [])
        has_activity = bool(info["commits"]) or bool(sims) or info["self_heal_count"] > 0
        if not has_activity:
            continue
        # 비즈니스 라벨: 카테고리 → 한국어 친화 변환
        cat_labels = []
        for c in info["categories"]:
            if "시뮬" in c: cat_labels.append("시뮬 작업")
            elif "로그" in c: cat_labels.append("테스트·메트릭")
            elif "히스토리" in c: cat_labels.append("문서 갱신")
            elif "주간정리" in c: cat_labels.append("주간 정리")
            elif "보고서" in c or "메일" in c: cat_labels.append("보고")
            elif "결정" in c: cat_labels.append("아키텍처 결정")
            elif "데이터" in c: cat_labels.append("데이터 수집")
            elif "학습" in c: cat_labels.append("학습")
            elif "테스트" in c: cat_labels.append("테스트")
            else: cat_labels.append(c)
        # commit 이 도구 작업뿐이라 cat_labels 비었지만 sim_task 가 있으면 "시뮬 작업" 으로 표시
        if not cat_labels and sims:
            cat_labels = ["시뮬 작업"]
        elif not cat_labels and info["self_heal_count"] > 0:
            cat_labels = ["자가치유"]
        cat_labels = sorted(set(cat_labels))

        timeline.append({
            "date": date,
            "commit_count": len(info["commits"]),
            "self_heal_count": info["self_heal_count"],
            "categories": cat_labels,
            "summary": " · ".join(cat_labels) if cat_labels else "기타",
            "commits": info["commits"][:8],  # 너무 길지 않게
            "sim_task_titles": [t.get("title", "")[:80] for t in sims[:3]],
            "phase_label": d.get("phase_label", ""),
            "scripts_run": d.get("scripts", [])[:5],
            "self_heal_actions": d.get("self_heal_actions", [])[:3],
        })
    return timeline


def _build_chart_stats(
    sim_tasks: list[dict], daily: list[dict], phases: list[dict],
    category_counts: dict,
) -> dict:
    """Hdel template.html 의 차트 함수 (drawHeatmap/AppBar/Donut/Trend/CatChart) 가
    기대하는 형식으로 데이터 emit. 분석 페이지 + 홈 차트가 채워지도록.
    """
    today = datetime.now(KST).date()

    # heatmap: 최근 60일 일별 활동 강도 + 주요 항목 (tooltip 용).
    # 형식: [{date, count, level, items: [title, ...]}], items 비면 tooltip 안 뜸.
    heatmap = []
    by_date_items: dict[str, list[str]] = {}
    for t in sim_tasks:
        if t.get("date"):
            ttl = (t.get("title") or "").strip()
            if ttl:
                by_date_items.setdefault(t["date"], []).append(ttl)
    for r in daily:
        if r.get("date"):
            ttl = (r.get("title") or "").strip()
            if ttl:
                by_date_items.setdefault(r["date"], []).append(ttl)
    for i in range(60):
        d = (today - timedelta(days=59 - i)).isoformat()
        items = by_date_items.get(d, [])
        count = len(items)
        heatmap.append({
            "date": d,
            "count": count,
            "level": min(count, 4),
            "items": items[:3],  # 최대 3개 (tooltip 길이 제한)
        })

    # appbar: phase 별 (n=완료, d=미완료). drawAppBar 는 a.name / a.n / a.d 사용.
    appbar = []
    for p in phases:
        if p.get("total", 0) == 0:
            continue
        appbar.append({
            "name": p["name"].replace(" — ", " ")[:20],
            "n": p.get("done", 0),
            "d": max(0, p.get("total", 0) - p.get("done", 0)),
        })

    # donut: 카테고리 분포 상위 3개 + 기타. drawDonut 은 {label, value} 사용.
    sorted_cats = sorted(category_counts.items(), key=lambda x: -x[1])
    donut = [{"label": k, "value": v} for k, v in sorted_cats[:3]]
    other = sum(v for _, v in sorted_cats[3:])
    if other:
        donut.append({"label": "기타", "value": other})

    # trend: 최근 30일 일별 카운트. drawTrend 는 d.w / d.n / d.d 사용.
    trend = []
    for i in range(30):
        d = today - timedelta(days=29 - i)
        ds = d.isoformat()
        n_sim = sum(1 for t in sim_tasks if t.get("date") == ds)
        n_daily = sum(1 for r in daily if r.get("date") == ds)
        if i % 3 == 0 or n_sim or n_daily:  # 빈 라벨 줄이기
            trend.append({"w": d.strftime("%m/%d"), "n": n_sim, "d": n_daily})

    # catChart: 카테고리 top 8. drawCatChart 는 it.name / it.v 사용 (단색 가로 바).
    catChart = [{"name": k, "v": v} for k, v in sorted_cats[:8]]

    # hot: 최근 sim_task 5개 id (sim_tasks 가 date desc 정렬되어 있음).
    hot = [t["id"] for t in sim_tasks[:5]]

    return {
        "heatmap": heatmap,
        "appbar": appbar,
        "donut": donut,
        "trend": trend,
        "catChart": catChart,
        "hot": hot,
    }


def compute_stats(sim_tasks: list[dict], daily: list[dict], blockers: list[dict]) -> dict:
    cat_counter: Counter = Counter()
    for t in sim_tasks:
        for c in (t.get("category") or "General").split(" · "):
            cat_counter[c] += 1

    # 최근 30일 자가치유 카운트
    today = datetime.now(KST).date()
    cutoff_30d = today - timedelta(days=30)
    self_heal_30d = sum(
        len(d.get("self_heal_actions", [])) for d in daily
        if d.get("date") and d["date"] >= cutoff_30d.isoformat()
    )

    # 최근 7일 커밋 속도 (commits/day)
    log_out = run(
        ["git", "log", "--since=7 days ago", "--pretty=oneline"],
        cwd=REPO_ROOT, timeout=10,
    )
    commits_7d = len([l for l in log_out.splitlines() if l.strip()])
    commit_velocity = round(commits_7d / 7.0, 2)

    blockers_active = sum(1 for b in blockers if not b.get("checked"))

    return {
        "total_sim_tasks": len(sim_tasks),
        "total_daily_entries": len(daily),
        "category_distribution": dict(cat_counter),
        "self_heal_count_30d": self_heal_30d,
        "commits_7d": commits_7d,
        "commit_velocity_7d": commit_velocity,
        "blockers_total": len(blockers),
        "blockers_active": blockers_active,
    }


# ─────────────────────────────────────────────────────────────────────────────
# meta
# ─────────────────────────────────────────────────────────────────────────────

def build_meta(current_phase: str) -> dict:
    head = run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, timeout=5).strip()
    last_commit = run(["git", "log", "-1", "--pretty=%s"], cwd=REPO_ROOT, timeout=5).strip()
    return {
        "built_at": datetime.now(KST).isoformat(timespec="seconds"),
        "repo_head": head or "(unknown)",
        "last_commit": last_commit[:120],
        "today": datetime.now(KST).strftime("%Y-%m-%d"),
        "current_phase": current_phase,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 합성
# ─────────────────────────────────────────────────────────────────────────────

def build_real_data() -> dict:
    phases, current_phase = build_phase_roadmap()
    sim_tasks = build_sim_tasks()
    daily = build_daily()
    evidence = build_evidence()
    blockers = build_blockers()
    samples = build_samples()
    decisions = build_decisions()
    stats = compute_stats(sim_tasks, daily, blockers)
    # Hdel template 의 차트 함수 호환 키 보강 (heatmap/appbar/donut/trend/catChart/hot)
    stats.update(_build_chart_stats(sim_tasks, daily, phases, stats.get("category_distribution", {})))

    # R2: 비즈니스 KPI / 월별 보고서 / 영상 / 활동 타임라인
    business_kpi = build_business_kpi(phases)
    monthly_reports = build_monthly_reports()
    videos = build_videos()
    hardware_photos = build_hardware_photos()
    training_metrics = build_training_metrics()
    inference_progress = build_inference_progress()
    activity_timeline = build_activity_timeline(daily, sim_tasks)

    data = {
        "meta": build_meta(current_phase),
        "vision": PROJECT_VISION,           # 정적 비전 정보
        "business_kpi": business_kpi,        # R2 신규
        "phases": phases,                    # 각 phase 에 business_label / outcome / report_label 포함
        "sim_tasks": sim_tasks,
        "daily": daily,
        "evidence": evidence,
        "blockers": blockers,
        "samples": samples,
        "decisions": decisions,
        "monthly_reports": monthly_reports,  # R2: Obsidian 풀 임베드
        "videos": videos,                    # R2: 시각 자산
        "hardware_photos": hardware_photos,  # 하드웨어 시각자료
        "training_metrics": training_metrics,  # PROG-2: ACT 학습 메트릭
        "inference_progress": inference_progress,  # PROG-2: 학습 진척 inference 영상
        "activity_timeline": activity_timeline,  # R2: 날짜별 그룹
        "stats": stats,
    }
    # Hdel template.html 호환 alias (기존 render* 함수가 새 키 모르므로)
    data["proposals"] = sim_tasks
    data["apps"] = phases
    data["magazines"] = evidence
    return data


# ─────────────────────────────────────────────────────────────────────────────
# 출력
# ─────────────────────────────────────────────────────────────────────────────

def render(data: dict, out: Path) -> Path:
    if not TEMPLATE_PATH.exists():
        raise SystemExit(
            f"template.html 없음: {TEMPLATE_PATH}\n"
            f"  Phase 1 MVP 다음 라운드에서 작성 예정. 지금은 --json-only 로 빌드.\n"
            f"  예: python3 {Path(__file__).name} --json-only"
        )
    tpl = TEMPLATE_PATH.read_text(encoding="utf-8")
    if DATA_MARKER not in tpl:
        raise SystemExit(f"template 에 {DATA_MARKER} 마커 없음")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    pattern = re.escape(DATA_MARKER) + r"\{[^\n]*?\};"
    if not re.search(pattern, tpl):
        raise SystemExit(f"template 의 데이터 라인 매칭 실패. 한 줄로 유지하세요.")
    replacement = DATA_MARKER + payload + ";"
    html = re.sub(pattern, lambda _: replacement, tpl, count=1)
    out.write_text(html, encoding="utf-8")
    return out


def write_json(data: dict, out: Path) -> Path:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    out.write_text(payload, encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--open", dest="open_after", action="store_true", help="빌드 후 브라우저로 열기")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"HTML 출력 경로 (기본: {DEFAULT_OUT})")
    parser.add_argument("--json", dest="emit_json", action="store_true",
                        help=f"(deprecated: 기본 동작) data.json 도 함께 출력 (기본 경로: {DEFAULT_JSON_OUT})")
    parser.add_argument("--no-json", dest="no_json", action="store_true",
                        help="data.json 출력 생략 (HTML 만 빌드). 기본은 HTML + JSON 둘 다.")
    parser.add_argument("--json-only", action="store_true",
                        help="HTML 생략, data.json 만 출력 (template.html 없는 단계에 권장)")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT,
                        help=f"data.json 출력 경로 (기본: {DEFAULT_JSON_OUT})")
    args = parser.parse_args()

    data = build_real_data()
    n_sim = len(data["sim_tasks"])
    n_daily = len(data["daily"])
    n_phases = len(data["phases"])
    n_blockers = len(data["blockers"])

    # default: HTML + JSON 둘 다. --no-json 또는 --json-only 로 한쪽만.
    emit_json = (not args.no_json) or args.emit_json or args.json_only
    emit_html = not args.json_only

    summary: list[str] = []
    if emit_html:
        out = render(data, args.out.resolve())
        try:
            rel = out.relative_to(REPO_ROOT)
        except ValueError:
            rel = out
        summary.append(f"HTML {rel} ({out.stat().st_size:,}B)")
    if emit_json:
        jout = write_json(data, args.json_out.resolve())
        try:
            jrel = jout.relative_to(REPO_ROOT)
        except ValueError:
            jrel = jout
        summary.append(f"JSON {jrel} ({jout.stat().st_size:,}B)")

    print(f"✓ Dashboard 빌드 완료: " + " · ".join(summary))
    print(f"  phases={n_phases}  sim_tasks={n_sim}  daily={n_daily}  blockers={n_blockers}")
    print(f"  current: {data['meta']['current_phase']}")

    if args.open_after and emit_html:
        webbrowser.open(args.out.resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
