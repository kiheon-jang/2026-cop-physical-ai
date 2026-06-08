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

# Phase 메타 — PHASE_ROADMAP 보다 안정적인 hard-coded label (월별 매핑은 README/PHASE_ROADMAP 의 사실)
PHASE_META: list[dict] = [
    {"id": "phase0", "name": "Phase 0 — 시뮬 환경 셋업",      "month": "2026-05", "weeks": 4},
    {"id": "phase1", "name": "Phase 1 — 사전학습",            "month": "2026-06", "weeks": 4},
    {"id": "phase2", "name": "Phase 2 — Sim2Real 검증",       "month": "2026-07", "weeks": 4},
    {"id": "phase3", "name": "Phase 3 — PCB 조정",            "month": "2026-08", "weeks": 4},
    {"id": "phase4", "name": "Phase 4 — RS232 HHT 결선",      "month": "2026-09", "weeks": 4},
    {"id": "phase5", "name": "Phase 5 — 통합 시연",           "month": "2026-10", "weeks": 4},
]

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

    phases: list[dict] = []
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
            # 월별 매핑 (PHASE_META 참조): 5월=phase0, 6월=phase1, 7월=phase2, ...
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

def _build_chart_stats(
    sim_tasks: list[dict], daily: list[dict], phases: list[dict],
    category_counts: dict,
) -> dict:
    """Hdel template.html 의 차트 함수 (drawHeatmap/AppBar/Donut/Trend/CatChart) 가
    기대하는 형식으로 데이터 emit. 분석 페이지 + 홈 차트가 채워지도록.
    """
    today = datetime.now(KST).date()

    # heatmap: 최근 60일 일별 활동 카운트 (sim_task + daily). [int, ...].
    heatmap = []
    by_date: dict[str, int] = {}
    for t in sim_tasks:
        if t.get("date"):
            by_date[t["date"]] = by_date.get(t["date"], 0) + 1
    for r in daily:
        if r.get("date"):
            by_date[r["date"]] = by_date.get(r["date"], 0) + 1
    for i in range(60):
        d = (today - timedelta(days=59 - i)).isoformat()
        heatmap.append(min(by_date.get(d, 0), 4))

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
    data = {
        "meta": build_meta(current_phase),
        "phases": phases,
        "sim_tasks": sim_tasks,
        "daily": daily,
        "evidence": evidence,
        "blockers": blockers,
        "samples": samples,
        "decisions": decisions,
        "stats": stats,
    }
    # Hdel template.html 호환 alias — 기존 render* 함수가 새 키 모르므로 같은 데이터를 옛 키로도 노출.
    # CoP 만의 신규 데이터 (blockers/samples/decisions) 는 별도 render 함수로 처리.
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
                        help=f"data.json 도 함께 출력 (기본 경로: {DEFAULT_JSON_OUT})")
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

    emit_json = args.emit_json or args.json_only
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
