#!/usr/bin/env python3
"""CoP Physical AI 일일 보고 메일 생성 + 발송 (시뮬 트랙).

2026-05-04 v3:
- 🆕 "오늘의 한 줄" 섹션 (Gemini API 자동 생성, 비전공자 친화)
- Vol → "Day N · D-N (시연까지)" 형식
- 프로그레스바 → Phase별 진행률 (전체가 아닌)
- 마크다운 `**...**` leak 수정
- "Phase X - WX" placeholder 정확 파싱
- __pycache__/.pyc 자동생성 파일 제외
- 시뮬 단계 카드 → 매주 월요일만
- 내일 예정 → PHASE_ROADMAP.md 동적 파싱
- 빠른 링크 4개 (8 → 4)

실행:
  /Users/markmini/Documents/dev/2026-cop-physical-ai/.venv/bin/python3 scripts/daily-report/generate_daily_report.py
"""
import datetime
import json
import os
import re
import smtplib
import subprocess
import sys
import urllib.request
import urllib.error
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE_PATH = REPO_ROOT / "docs/01_overview/mail-template.html"
START_DATE = datetime.date(2026, 4, 21)
DEMO_DATE = datetime.date(2026, 10, 31)  # 10월 시연 D-day
KST = datetime.timezone(datetime.timedelta(hours=9))


# =============================================================================
# 유틸리티
# =============================================================================

def _load_smtp_env_from_hermes():
    """~/.hermes/.env에서 EMAIL_*, GEMINI_API_KEY를 os.environ에 로드."""
    env_path = os.path.expanduser("~/.hermes/.env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            if not (key.startswith("EMAIL_") or key in ("GEMINI_API_KEY", "GOOGLE_API_KEY")):
                continue
            if key in os.environ:
                continue
            value = value.strip().strip('"').strip("'")
            os.environ[key] = value


def run(cmd, cwd=None):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           cwd=cwd or str(REPO_ROOT), timeout=30)
        return r.stdout.strip(), r.returncode
    except Exception:
        return "", 1


def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return ""


def html_escape(text):
    if not text:
        return ""
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


def safe_html_with_br(text):
    """텍스트는 escape, <br/> 태그만 복원 (LLM이 줄바꿈으로 사용한 것)."""
    if not text:
        return ""
    escaped = html_escape(text)
    for variant in ("&lt;br/&gt;", "&lt;br /&gt;", "&lt;br&gt;"):
        escaped = escaped.replace(variant, "<br/>")
    return escaped


def strip_markdown(text):
    """마크다운 마커(`**`, `*`, backtick) 제거."""
    if not text:
        return ""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    return text


# =============================================================================
# 헤더 정보 (Day N · D-N 형식)
# =============================================================================

def get_header_info():
    today_dt = datetime.datetime.now(KST)
    today = today_dt.date()
    day_num = (today - START_DATE).days + 1
    d_minus = (DEMO_DATE - today).days
    days = ["월", "화", "수", "목", "금", "토", "일"]
    weekday = days[today.weekday()]
    return {
        "vol_label": f"Day {day_num} · D-{d_minus}",
        "today_date_full": f"{today.strftime('%Y-%m-%d')} ({weekday})",
        "today_date": today.strftime("%Y-%m-%d"),
        "yesterday": (today - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
        "weekday_idx": today.weekday(),  # 0=월
        "today": today,
    }


# =============================================================================
# Phase 진행도 — Phase별 (전체가 아닌)
# =============================================================================

PHASES = [
    ("Phase 0", "5월 시뮬 환경 셋업", datetime.date(2026, 5, 1), datetime.date(2026, 5, 31), [
        ("W1", datetime.date(2026, 5, 1), datetime.date(2026, 5, 7), "MuJoCo + 모델 import"),
        ("W2", datetime.date(2026, 5, 8), datetime.date(2026, 5, 14), "카메라 시뮬 셋업"),
        ("W3", datetime.date(2026, 5, 15), datetime.date(2026, 5, 21), "실기↔시뮬 매핑 검증"),
        ("W4", datetime.date(2026, 5, 22), datetime.date(2026, 5, 31), "Pick-Place + 데이터셋"),
    ]),
    ("Phase 1", "6월 시뮬 데이터 + ACT 사전학습", datetime.date(2026, 6, 1), datetime.date(2026, 6, 30), []),
    ("Phase 2", "7월 Sim2Real 검증", datetime.date(2026, 7, 1), datetime.date(2026, 7, 31), []),
    ("Phase 3", "8월 PCB 조정 시뮬 학습", datetime.date(2026, 8, 1), datetime.date(2026, 8, 31), []),
    ("Phase 4", "9월 RS232 결선 시뮬 학습", datetime.date(2026, 9, 1), datetime.date(2026, 9, 30), []),
    ("Phase 5", "10월 통합 시연", datetime.date(2026, 10, 1), datetime.date(2026, 10, 31), []),
]


def get_phase_progress(today):
    cur = None
    cur_week = None
    week_desc = ""
    next_milestone = ""
    for name, label, start, end, weeks in PHASES:
        if start <= today <= end:
            cur = (name, label, start, end)
            for i, (w_name, w_start, w_end, w_desc) in enumerate(weeks):
                if w_start <= today <= w_end:
                    cur_week = w_name
                    week_desc = w_desc
                    if i + 1 < len(weeks):
                        nm = weeks[i + 1]
                        next_milestone = f"다음 마일스톤: {nm[1].strftime('%-m/%-d')} — {nm[3]}"
                    else:
                        next_milestone = f"다음: {end.strftime('%-m/%-d')} {name} 종료 → 다음 Phase"
                    break
            break

    if cur:
        days_in_phase = (cur[3] - cur[2]).days + 1
        days_done = (today - cur[2]).days + 1
        pct = max(0, min(100, int(days_done / days_in_phase * 100)))
        title = f"{cur[0]} — {cur[1]}"
        count = f"{cur_week or '-'} · Day {days_done}/{days_in_phase} ({pct}%)"
        if not next_milestone:
            next_milestone = f"오늘 {today.strftime('%Y-%m-%d')} · Phase 종료 {cur[3].strftime('%-m/%-d')}"
    else:
        title = "Phase 미정"
        count = "-"
        pct = 0
        next_milestone = ""

    return {"title": title, "count": count, "percent": pct, "milestone": next_milestone}


# =============================================================================
# 🆕 오늘의 한 줄 — Gemini API로 비전공자 친화 설명 자동 생성
# =============================================================================

def gemini_call(prompt, max_tokens=400, temperature=0.6):
    """Gemini 2.5 Flash 직접 호출. 실패 시 None."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": temperature,
            "thinkingConfig": {"thinkingBudget": 0},  # thinking 끔 (응답 보장)
        },
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read())
        cands = d.get("candidates", [])
        if not cands:
            return None
        text = cands[0]["content"]["parts"][0].get("text", "").strip()
        return text or None
    except Exception:
        return None


def get_headline_html(yesterday):
    """비전공자 임원 친화적 한 줄 + 2-3줄 설명 + 왜 중요한가."""
    log_path = REPO_ROOT / f"agent/research-log/{yesterday}.md"
    log_content = read_text(log_path)
    if not log_content:
        # research-log 없으면 어제 git 커밋으로 fallback
        commits_text, _ = run("git log --since='1 day ago' --pretty=format:'%s%n%b' | head -50")
        log_content = commits_text

    if not log_content:
        return {
            "oneliner": "어제 작업 없음",
            "detail": "어제 자동 작업 기록이 없습니다.",
            "why": "오늘부터 다시 시뮬 환경 단계별 구축이 자동 진행됩니다.",
        }

    # Gemini에게 비전공자 친화 설명 요청
    prompt = f"""당신은 로보틱스 프로젝트의 일일 보고를 회사 임원진(비전공자)에게 전달하는 매거진 에디터입니다.

다음은 어제 자동 작업 로그입니다:

```
{log_content[:1500]}
```

위 내용을 다음 3가지로 요약해주세요. 반드시 아래 JSON 형식으로만 답하세요. 다른 텍스트 금지.

{{
  "oneliner": "한 줄 요약 (50자 이내, 비전공자도 이해할 수 있게)",
  "detail": "어떤 의미냐면 - 으로 시작하는 2-3줄 쉬운 설명. 게임/일상 비유 활용 가능. HTML <br/> 태그로 줄바꿈.",
  "why": "왜 중요한가? 10월 PCB 조정 + RS232 HHT 결선 시연 목표와 어떻게 연결되는지 1-2문장."
}}

조건:
- 전문용어 최소화. 'MuJoCo'는 '시뮬레이션 엔진'으로 풀어 쓰기 가능
- '컴퓨터 안의 가상 로봇' 같은 일상 표현 우선
- 따뜻하고 자신감 있는 톤. 진척이 있다면 그 가치를 명확히
- '~했습니다'체 사용
"""
    response = gemini_call(prompt, max_tokens=600, temperature=0.6)

    if response:
        # JSON 추출
        m = re.search(r"\{.*\}", response, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(0))
                return {
                    "oneliner": data.get("oneliner", "오늘의 진척").strip(),
                    "detail": data.get("detail", "").strip(),
                    "why": data.get("why", "").strip(),
                }
            except json.JSONDecodeError:
                pass

    # Gemini 실패 시 fallback (research-log에서 직접 추출)
    summary = ""
    m = re.search(r"## 오늘 진행 단계\s*\n+(.+?)(?=\n##|\Z)", log_content, re.DOTALL)
    if m:
        summary = m.group(1).strip().split("\n")[0].strip()
    return {
        "oneliner": summary[:60] if summary else "어제 시뮬 작업 진행",
        "detail": "어제 자동 작업으로 시뮬레이션 환경이 한 단계 더 구축됐습니다.",
        "why": "10월 PCB 조정 + RS232 HHT 결선 시연을 향한 매일의 작은 진척입니다.",
    }


# =============================================================================
# 어제 커밋 (노이즈 제외)
# =============================================================================

NOISE_PATTERNS = [
    "__pycache__",
    ".pyc",
    ".DS_Store",
    "node_modules",
]

TYPE_PATTERNS = [
    ("RESEARCH", ["research", "초안", "drafts", "🔬"]),
    ("SIM", ["시뮬", "[시뮬]", "simulation", "🛠"]),
    ("LOG", ["로그", "[로그]", "메트릭", "📊"]),
    ("DOCS", ["docs", "문서", "📝", "📋"]),
    ("FIX", ["fix", "버그", "🔧"]),
]

TYPE_CLASS = {
    "RESEARCH": "type-research",
    "SIM": "type-sample",
    "LOG": "type-sample",
    "DOCS": "type-docs",
    "FIX": "type-fix",
}


def classify_commit(msg):
    msg_low = msg.lower()
    for t, patterns in TYPE_PATTERNS:
        for p in patterns:
            if p in msg_low or p in msg:
                return t
    return "DOCS"


def filter_noise(paths):
    return [p for p in paths if not any(n in p for n in NOISE_PATTERNS)]


def get_yesterday_commits():
    out, rc = run("git log --since='1 day ago' --pretty=format:'%s|||%H' -20")
    if rc != 0 or not out:
        return [], 0
    commits = []
    for line in out.split("\n"):
        if not line or "|||" not in line:
            continue
        msg, sha = line.split("|||", 1)
        sha = sha.strip()[:7]
        files_out, _ = run(f"git show --name-only --pretty=format: {sha}")
        files = filter_noise([f for f in files_out.split("\n") if f.strip()])[:2]
        files_str = " · ".join(files) if files else ""
        commits.append({
            "msg": strip_markdown(msg.strip()),
            "sha": sha,
            "files": files_str,
            "type": classify_commit(msg),
        })
    return commits, len(commits)


def commits_to_html(commits):
    if not commits:
        return '<div class="no-issue">어제 작업 없음</div>'
    items = []
    for i, c in enumerate(commits, 1):
        title = html_escape(c["msg"])
        files = html_escape(c["files"])
        cls = TYPE_CLASS.get(c["type"], "type-docs")
        items.append(f'''<div class="task-item">
      <div class="task-num">{i}</div>
      <div class="task-content">
        <div><span class="task-type {cls}">{c["type"]}</span><span class="task-title">{title}</span></div>
        {'<div class="task-path">' + files + '</div>' if files else ''}
      </div>
    </div>''')
    return "\n    ".join(items)


# =============================================================================
# 시뮬 진척 (research-log) — placeholder 정확 파싱
# =============================================================================

def get_sim_progress_html(yesterday, header_info):
    log_path = REPO_ROOT / f"agent/research-log/{yesterday}.md"
    if not log_path.exists():
        return '<div class="no-issue">어제 시뮬 진척 기록 없음</div>'
    content = read_text(log_path)

    # 단계명 추출 — "Phase X - WX" 형식이면 실제 Phase로 치환
    phase_step = "Phase 진행 중"
    m = re.search(r"## 오늘 진행 단계\s*\n+(.+?)(?=\n##|\Z)", content, re.DOTALL)
    if m:
        first = m.group(1).strip().split("\n")[0].strip()
        # "Phase X - WX - 6-DoF" 같은 placeholder 치환
        if re.search(r"Phase\s+X|WX", first):
            phase_progress = get_phase_progress(header_info["today"])
            actual_phase = phase_progress["title"].split(" — ")[0]  # "Phase 0"
            actual_week = phase_progress["count"].split(" ")[0]      # "W1"
            # 마지막 부분만 (실제 단계 설명)
            tail = re.sub(r"^.*?-\s*", "", first) if " - " in first else first
            phase_step = f"{actual_phase} {actual_week} — {tail}".strip()
        else:
            phase_step = strip_markdown(first)

    # 메트릭 추출
    metrics = ""
    m2 = re.search(r"## 실행 테스트 결과\s*\n+(.+?)(?=\n##|\Z)", content, re.DOTALL)
    if m2:
        metrics = strip_markdown(m2.group(1).strip())

    return f'''<div class="research-summary">
      <div class="research-topic">{html_escape(phase_step)}</div>
      <div class="research-oneliner">상세 로그 → <code>agent/research-log/{yesterday}.md</code></div>
    </div>
    <div class="why-card">
      <pre style="margin:0;font-size:11px;color:#94a3b8;white-space:pre-wrap;font-family:monospace;">{html_escape(metrics[:400])}</pre>
    </div>'''


# =============================================================================
# 이슈 (마크다운 제거)
# =============================================================================

def get_issues_html(yesterday):
    log_path = REPO_ROOT / f"agent/research-log/{yesterday}.md"
    content = read_text(log_path)
    if not content:
        return '<div class="no-issue">현재 이슈 없음</div>'
    m = re.search(r"## 관찰 / 이슈\s*\n+(.+?)(?=\n##|\Z)", content, re.DOTALL)
    if not m:
        return '<div class="no-issue">현재 이슈 없음</div>'
    issues_text = strip_markdown(m.group(1).strip())
    if not issues_text or "없음" in issues_text[:20]:
        return '<div class="no-issue">현재 이슈 없음</div>'
    items = []
    for line in issues_text.split("\n"):
        line = line.strip().lstrip("- ").strip()
        if line:
            items.append(f'<div class="issue-item">{html_escape(line)}</div>')
    return "\n    ".join(items) if items else '<div class="no-issue">현재 이슈 없음</div>'


# =============================================================================
# 외부 의존 — 마크다운 제거 + 만료 마감일 강조
# =============================================================================

def get_external_deps_html(today):
    deps = read_text(REPO_ROOT / "agent/external-dependencies.md")
    if not deps:
        return '<div class="no-issue">외부 의존 항목 없음</div>'
    m = re.search(r"## 🔴 진행중.+?(?=\n## |\Z)", deps, re.DOTALL)
    section = m.group(0) if m else deps
    items = []
    for match in re.finditer(r"-\s*\[\s*\]\s*(.+?)(?=\n-\s*\[|\n##|\Z)", section, re.DOTALL):
        body = match.group(1).strip()
        first_line = strip_markdown(body.split("\n", 1)[0].strip())
        title_html = html_escape(first_line[:120])
        deadline_m = re.search(r"마감[:\s]+(\d{4}-\d{2}-\d{2})", body)
        deadline_str = ""
        if deadline_m:
            try:
                dl = datetime.datetime.strptime(deadline_m.group(1), "%Y-%m-%d").date()
                days_left = (dl - today).days
                if days_left < 0:
                    deadline_str = f' <span style="color:#ef4444;font-size:11px;font-weight:700;">⚠ 마감 초과 ({deadline_m.group(1)})</span>'
                elif days_left <= 7:
                    deadline_str = f' <span style="color:#ef4444;font-size:11px;font-weight:700;">⏰ D-{days_left}</span>'
                else:
                    deadline_str = f' <span style="color:#f59e0b;font-size:11px;">D-{days_left}</span>'
            except ValueError:
                pass
        items.append(f'''<div class="action-item">
      <span class="action-dot">📌</span>
      <span class="action-text">{title_html}{deadline_str}</span>
    </div>''')
    return "\n    ".join(items) if items else '<div class="no-issue">미해결 외부 의존 없음</div>'


def get_pending_decisions_html():
    decisions_md = read_text(REPO_ROOT / "research/decisions/README.md")
    items = []
    in_pending = False
    for line in decisions_md.split("\n"):
        if "현재 검토 대기" in line:
            in_pending = True
            continue
        if in_pending and line.startswith("###"):
            break
        if in_pending and "|" in line and "🔄" in line:
            cols = [c.strip() for c in line.split("|")]
            if len(cols) >= 3:
                topic_full = cols[1]
                if "—" in topic_full:
                    topic, desc = topic_full.split("—", 1)
                else:
                    topic, desc = topic_full, ""
                topic = strip_markdown(topic.strip())
                desc = strip_markdown(desc.strip())
                items.append(f'<div class="pending-item"><div class="pending-dot"></div><span class="pending-label">{html_escape(topic)}</span><span class="pending-arrow">→</span><span class="pending-desc">{html_escape(desc)}</span></div>')
    return "\n      ".join(items) if items else '<div class="pending-item"><span class="pending-desc" style="color:#64748b;">결정 대기 항목 없음</span></div>'


# =============================================================================
# Phase 단계 카드 — 매주 월요일만 (반복 노이즈 제거)
# =============================================================================

def get_phase_details(today, weekday_idx):
    phase_progress = get_phase_progress(today)

    # 월요일이 아니면 빈 섹션 (HTML 자체를 빈 태그로)
    show_card = (weekday_idx == 0)  # 월요일

    if today.month == 5:
        topic = "Phase 0 — MuJoCo 시뮬 환경 셋업"
        oneliner = "MuJoCo + SO-ARM101 MJCF 모델로 시뮬레이션 환경을 구축하고, viewer로 6-DoF 동작을 검증합니다."
        why = "Mac Mini M5 단독으로 Phase 0~5(5~10월)를 진행하기 위한 환경. 실기 카메라 없이 시뮬 가상 카메라만 사용."
        steps = [
            ("01", "MuJoCo 3.x", "Apple Silicon 네이티브 패키지로 한 줄 설치, 환경변수 불필요"),
            ("02", "SO-ARM100/101 MJCF", "TheRobotStudio 공식 모델, 6-DoF 관절 + 그리퍼"),
            ("03", "viewer + Renderer", "macOS Metal 백엔드로 직접 시뮬 동작 검증"),
        ]
    elif today.month == 6:
        topic = "Phase 1 — 시뮬 데이터 + ACT 사전학습"
        oneliner = "시뮬 200 에피소드로 ACT 사전학습 → 실기 적은 데이터로 fine-tune합니다."
        why = "보고용 6월 계획(텔레오퍼레이션 검증)에 더해 실제로는 학습 단계 진입."
        steps = [
            ("01", "200 에피소드 합성", "시뮬에서 자동 데이터 생성"),
            ("02", "ACT 사전학습", "epoch 100 학습, 손실 곡선 모니터링"),
            ("03", "실기 fine-tune", "5~10 에피소드로 실기 보정"),
        ]
    else:
        topic = phase_progress["title"]
        oneliner = phase_progress["count"]
        why = "Phase별 상세는 PHASE_ROADMAP.md 참조."
        steps = [("01", phase_progress["title"], phase_progress["count"])]

    if not show_card:
        # 매주 월요일만 큰 카드, 그 외엔 한 줄로 간략히
        return None  # 빈 섹션 처리

    steps_html = "\n      ".join([
        f'''<div class="concept-item">
        <div class="concept-num">{n}</div>
        <div>
          <div class="concept-name">{html_escape(name)}</div>
          <div class="concept-desc">{html_escape(desc)}</div>
        </div>
      </div>'''
        for n, name, desc in steps
    ])
    return {
        "header": "이번 주 시뮬 단계",
        "badge": phase_progress["title"].split(" — ")[0],
        "topic": topic,
        "oneliner": oneliner,
        "steps_html": steps_html,
        "why": why,
    }


# =============================================================================
# 시뮬/학습 스크립트 (어제 변경/추가된 것만)
# =============================================================================

def get_samples_html():
    # 어제 변경된 .py 파일만
    out, _ = run("git log --since='1 day ago' --name-only --pretty=format: -- 'samples/**/*.py' 'scripts/**/*.py'")
    paths = sorted(set(p for p in out.split("\n") if p.endswith(".py") and not any(n in p for n in NOISE_PATTERNS)))
    if not paths:
        return '<div class="no-issue">어제 변경된 스크립트 없음 — <a href="https://github.com/kiheon-jang/2026-cop-physical-ai/blob/main/samples/SAMPLE_STATUS.md" style="color:#6366f1;">전체 현황 →</a></div>'
    items = []
    for p in paths[:6]:
        name = Path(p).name
        parent = str(Path(p).parent)
        items.append(f'<div class="sample-item"><span class="stars">⭐</span><span class="sample-name">{html_escape(name)}</span><span class="sample-desc">{html_escape(parent)}</span></div>')
    return "\n    ".join(items)


def get_sample_review_html():
    return '''<div class="review-box">
      💡 모든 시뮬/학습 스크립트는 <code>.venv</code>에서 실행되어야 합니다.<br/>
      실행: <code>.venv/bin/python3 &lt;스크립트&gt;</code>
    </div>'''


# =============================================================================
# 경로 변경 (노이즈 제외)
# =============================================================================

def get_changes_html():
    out, _ = run("git log --since='1 day ago' --name-status --pretty=format:'---'")
    if not out:
        return '<div class="no-issue">변경 없음</div>'
    changes = {}
    for line in out.split("\n"):
        if not line or line == "---":
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0]
        path = parts[1]
        if any(n in path for n in NOISE_PATTERNS):
            continue
        if status.startswith("A"):
            changes[path] = "add"
        elif status.startswith("D"):
            changes[path] = "del"
        elif (status.startswith("R") or status.startswith("M")) and path not in changes:
            changes[path] = "move"
    if not changes:
        return '<div class="no-issue">변경 없음</div>'
    items = []
    for path, t in list(changes.items())[:8]:
        cls = {"add": "type-add", "move": "type-move", "del": "type-del"}.get(t, "type-add")
        label = {"add": "ADD", "move": "MOD", "del": "DEL"}[t]
        items.append(f'<div class="change-item"><span class="change-type {cls}">{label}</span><span class="change-path">{html_escape(path)}</span></div>')
    return "\n    ".join(items)


# =============================================================================
# 🎬 오늘의 결과물 — 어제 add된 미디어 파일 자동 추출 + GitHub 링크
# =============================================================================

MEDIA_EXT = {
    "video": [".mp4", ".webm", ".mov", ".avi"],
    "image": [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"],
    "pdf": [".pdf"],
}

MEDIA_ICON = {
    "video": "🎬",
    "image": "🖼",
    "pdf": "📄",
}

GITHUB_REPO = "kiheon-jang/2026-cop-physical-ai"


def get_media_artifacts():
    """어제 git에 add된 미디어 파일 목록 + GitHub 링크."""
    out, _ = run("git log --since='1 day ago' --diff-filter=A --name-only --pretty=format:")
    if not out:
        return []
    paths = sorted(set(p for p in out.split("\n") if p.strip()))

    items = []
    for path in paths:
        ext = Path(path).suffix.lower()
        media_type = None
        for t, exts in MEDIA_EXT.items():
            if ext in exts:
                media_type = t
                break
        if not media_type:
            continue

        # 실제 파일 존재 확인 + 크기
        full_path = REPO_ROOT / path
        if not full_path.exists():
            continue
        size_bytes = full_path.stat().st_size
        if size_bytes < 1024:
            size_str = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes // 1024} KB"
        else:
            size_str = f"{size_bytes / (1024*1024):.1f} MB"

        items.append({
            "path": path,
            "name": Path(path).name,
            "type": media_type,
            "size": size_str,
            "view_url": f"https://github.com/{GITHUB_REPO}/blob/main/{path}",
            "raw_url": f"https://github.com/{GITHUB_REPO}/raw/main/{path}",
        })
    return items


def get_media_section_html():
    """🎬 오늘의 결과물 섹션 — 미디어 없으면 섹션 자체 비표시."""
    items = get_media_artifacts()
    if not items:
        return ""  # 빈 섹션 (HTML 자체가 안 보임)

    cards = []
    for it in items[:6]:
        icon = MEDIA_ICON[it["type"]]
        cta_label = {"video": "▶ 재생하기", "image": "🔍 크게 보기", "pdf": "📖 열기"}[it["type"]]
        cards.append(f'''<a href="{it["view_url"]}" class="media-card">
        <div class="media-icon">{icon}</div>
        <div class="media-name">{html_escape(it["name"])}</div>
        <div class="media-meta">{html_escape(it["path"])} · {it["size"]}</div>
        <div class="media-cta">{cta_label} →</div>
      </a>''')

    return f'''<div class="section">
    <div class="section-header">
      <span class="section-icon">🎬</span>
      <span class="section-title">오늘의 결과물</span>
      <span class="section-badge">{len(items)}건</span>
    </div>
    <div class="media-grid">
      {chr(10).join(cards)}
    </div>
  </div>'''


# =============================================================================
# 내일 예정 — PHASE_ROADMAP.md 동적 파싱
# =============================================================================

def get_tomorrow_html(today):
    tomorrow = today + datetime.timedelta(days=1)
    roadmap = read_text(REPO_ROOT / "research/simulation/PHASE_ROADMAP.md")

    # 해당 날짜의 작업 라인 찾기 — "**M/D**: 내용" 또는 "M/D: 내용"
    pattern = rf"[*\-\s]*\*?\*?{tomorrow.month}/{tomorrow.day}\*?\*?[:.\s]+(.+?)(?=\n[-\s]|\n\n|\Z)"
    m = re.search(pattern, roadmap)
    if m:
        next_step = strip_markdown(m.group(1).strip())[:80]
    else:
        # fallback: 현재 Phase의 다음 작업
        phase_progress = get_phase_progress(tomorrow)
        next_step = phase_progress["count"]

    return f'''<div class="schedule-item"><span class="schedule-tag tag-sample">시뮬 구축</span><span class="schedule-desc">{html_escape(next_step)}</span></div>
    <div class="schedule-item"><span class="schedule-tag tag-research">테스트</span><span class="schedule-desc">시뮬 메트릭 수집 + research-log 작성</span></div>
    <div class="schedule-item"><span class="schedule-tag tag-report">보고</span><span class="schedule-desc">일일 보고 메일 발송</span></div>'''


# =============================================================================
# 메일 발송
# =============================================================================

def send_email_smtp(recipient, subject, html_body):
    smtp_host = os.environ.get("EMAIL_SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("EMAIL_SMTP_PORT", "587"))
    sender = os.environ.get("EMAIL_ADDRESS")
    password = os.environ.get("EMAIL_PASSWORD")
    if not (sender and password):
        return False, "Missing EMAIL_ADDRESS / EMAIL_PASSWORD"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as s:
                s.login(sender, password)
                s.sendmail(sender, [recipient], msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as s:
                s.ehlo(); s.starttls(); s.ehlo()
                s.login(sender, password)
                s.sendmail(sender, [recipient], msg.as_string())
        return True, None
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


# =============================================================================
# 메인
# =============================================================================

def render_html():
    template = read_text(TEMPLATE_PATH)
    if not template:
        raise FileNotFoundError(f"Template not found: {TEMPLATE_PATH}")

    header = get_header_info()
    phase_progress = get_phase_progress(header["today"])
    commits, count = get_yesterday_commits()
    headline = get_headline_html(header["yesterday"])
    phase_details = get_phase_details(header["today"], header["weekday_idx"])

    placeholders = {
        "<!--TODAY_DATE-->": header["today_date_full"],
        "<!--PHASE_TITLE-->": phase_progress["title"],
        "<!--PROGRESS_COUNT-->": phase_progress["count"],
        "<!--PROGRESS_PERCENT-->": str(phase_progress["percent"]),
        "<!--MILESTONE-->": phase_progress["milestone"],
        "<!--HEADLINE_ONELINER-->": html_escape(headline["oneliner"]),
        "<!--HEADLINE_DETAIL-->": safe_html_with_br(headline["detail"]),
        "<!--HEADLINE_WHY-->": safe_html_with_br(headline["why"]),
        "<!--MEDIA_SECTION-->": get_media_section_html(),
        "<!--COMMITS_COUNT-->": f"{count}건",
        "<!--COMMITS_HTML-->": commits_to_html(commits),
        "<!--SIM_PROGRESS_HTML-->": get_sim_progress_html(header["yesterday"], header),
        "<!--ISSUES_HTML-->": get_issues_html(header["yesterday"]),
        "<!--EXTERNAL_DEPS_HTML-->": get_external_deps_html(header["today"]),
        "<!--PENDING_DECISIONS_HTML-->": get_pending_decisions_html(),
        "<!--SAMPLES_HTML-->": get_samples_html(),
        "<!--SAMPLE_REVIEW_HTML-->": get_sample_review_html(),
        "<!--CHANGES_HTML-->": get_changes_html(),
        "<!--TOMORROW_HTML-->": get_tomorrow_html(header["today"]),
    }

    # Phase 단계 카드 — 월요일만 표시, 그 외엔 빈 placeholder
    if phase_details:
        placeholders["<!--PHASE_HEADER-->"] = phase_details["header"]
        placeholders["<!--PHASE_BADGE-->"] = phase_details["badge"]
        placeholders["<!--PHASE_TOPIC-->"] = phase_details["topic"]
        placeholders["<!--PHASE_ONELINER-->"] = phase_details["oneliner"]
        placeholders["<!--PHASE_STEPS_HTML-->"] = phase_details["steps_html"]
        placeholders["<!--PHASE_WHY-->"] = phase_details["why"]
    else:
        # 월요일이 아니면 단계 카드 섹션 자체를 제거 (간단화: placeholder만 비움)
        placeholders["<!--PHASE_HEADER-->"] = "이번 주 시뮬 단계"
        placeholders["<!--PHASE_BADGE-->"] = phase_progress["title"].split(" — ")[0]
        placeholders["<!--PHASE_TOPIC-->"] = "이번 주 단계는 매주 월요일에 자세히 안내됩니다"
        placeholders["<!--PHASE_ONELINER-->"] = phase_progress["count"]
        placeholders["<!--PHASE_STEPS_HTML-->"] = ""
        placeholders["<!--PHASE_WHY-->"] = "PHASE_ROADMAP.md 에서 전체 로드맵 확인 가능."

    html = template
    for k, v in placeholders.items():
        html = html.replace(k, v)
    return html, header


def main():
    _load_smtp_env_from_hermes()
    html, header = render_html()

    out_dir = REPO_ROOT / "docs/01_overview/daily-reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{header['today_date']}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"[저장] {out_path}")

    test_mode = os.environ.get("EMAIL_TEST_MODE", "").lower() == "true"
    if test_mode:
        recipients = ["xaqwer@gmail.com"]
        print("[EMAIL_TEST_MODE=true] 본인(xaqwer)에게만 발송")
    else:
        recipients = [
            "xaqwer@gmail.com",
            "insoo.kum@hyundaielevator.com",
            "giheon.jang@hyundaielevator.com",
            "kimeun091473@gmail.com",
        ]
        print(f"[정상 발송] {len(recipients)}명")

    subject = f"[CoP Physical AI] 일일 연구 보고 | {header['today_date']}"

    success = 0
    for r in recipients:
        print(f"→ {r} ...", end=" ", flush=True)
        ok, err = send_email_smtp(r, subject, html)
        if ok:
            print("✅")
            success += 1
        else:
            print(f"❌ {err}")

    print(f"\n발송 결과: {success}/{len(recipients)} 성공")
    return 0 if success == len(recipients) else 1


if __name__ == "__main__":
    sys.exit(main())
