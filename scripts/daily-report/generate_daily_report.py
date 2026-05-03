#!/usr/bin/env python3
"""CoP Physical AI 일일 보고 메일 생성 + 발송 (시뮬 트랙).

2026-05-04 v2: 전면 재작성
- 표준 Python (hermes_tools 의존성 제거)
- mail-template.html placeholder 채우기 방식
- 시뮬 트랙 데이터 소스: research/simulation/, agent/research-log/, agent/external-dependencies.md
- Gmail SMTP 직접 발송 (send_email_smtp)
- EMAIL_TEST_MODE=true → 본인만 발송

실행:
  cd /Users/markmini/Documents/dev/2026-cop-physical-ai
  source .venv/bin/activate
  python3 scripts/daily-report/generate_daily_report.py
또는:
  /Users/markmini/Documents/dev/2026-cop-physical-ai/.venv/bin/python3 scripts/daily-report/generate_daily_report.py
"""
import datetime
import os
import re
import smtplib
import subprocess
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE_PATH = REPO_ROOT / "docs/01_overview/mail-template.html"
START_DATE = datetime.datetime(2026, 4, 21, tzinfo=datetime.timezone(datetime.timedelta(hours=9)))
KST = datetime.timezone(datetime.timedelta(hours=9))


# =============================================================================
# 유틸리티
# =============================================================================

def _load_smtp_env_from_hermes():
    """~/.hermes/.env에서 EMAIL_* 변수를 os.environ에 로드. 이미 있으면 덮어쓰지 않음."""
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
            if not key.startswith("EMAIL_"):
                continue
            if key in os.environ:
                continue
            value = value.strip().strip('"').strip("'")
            os.environ[key] = value


def run(cmd, cwd=None):
    """subprocess wrapper. (stdout, returncode)"""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           cwd=cwd or str(REPO_ROOT), timeout=30)
        return r.stdout.strip(), r.returncode
    except Exception:
        return "", 1


def read_text(path):
    """파일 내용 읽기. 실패 시 빈 문자열."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return ""


def html_escape(text):
    """HTML 특수문자 escape."""
    if not text:
        return ""
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


# =============================================================================
# 헤더 정보
# =============================================================================

def get_header_info():
    today = datetime.datetime.now(KST)
    delta = today - START_DATE
    vol_num = f"Vol.{delta.days + 1:03d}"
    days = ["월", "화", "수", "목", "금", "토", "일"]
    weekday = days[today.weekday()]
    today_date = today.strftime("%Y-%m-%d")
    yesterday = (today - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    return {
        "vol_num": vol_num,
        "today_date_full": f"{today_date} ({weekday})",
        "today_date": today_date,
        "yesterday": yesterday,
    }


# =============================================================================
# Phase 진행도 (PHASE_ROADMAP.md 기반)
# =============================================================================

def get_phase_progress(today_date):
    """현재 Phase/주차 식별 + 진행도 계산."""
    roadmap = read_text(REPO_ROOT / "research/simulation/PHASE_ROADMAP.md")
    today = datetime.datetime.strptime(today_date, "%Y-%m-%d").date()

    # 5월 W1~W4 매핑 (Phase 0)
    phases = [
        ("Phase 0", "5월", datetime.date(2026, 5, 1), datetime.date(2026, 5, 31), [
            ("W1", datetime.date(2026, 5, 1), datetime.date(2026, 5, 7), "MuJoCo + 모델 import"),
            ("W2", datetime.date(2026, 5, 8), datetime.date(2026, 5, 14), "카메라 시뮬 셋업"),
            ("W3", datetime.date(2026, 5, 15), datetime.date(2026, 5, 21), "실기↔시뮬 매핑 검증"),
            ("W4", datetime.date(2026, 5, 22), datetime.date(2026, 5, 31), "Pick-Place + 데이터셋"),
        ]),
        ("Phase 1", "6월", datetime.date(2026, 6, 1), datetime.date(2026, 6, 30), []),
        ("Phase 2", "7월", datetime.date(2026, 7, 1), datetime.date(2026, 7, 31), []),
        ("Phase 3", "8월", datetime.date(2026, 8, 1), datetime.date(2026, 8, 31), []),
        ("Phase 4", "9월", datetime.date(2026, 9, 1), datetime.date(2026, 9, 30), []),
        ("Phase 5", "10월", datetime.date(2026, 10, 1), datetime.date(2026, 10, 31), []),
    ]

    cur_phase = None
    cur_week = None
    week_desc = ""
    for name, label, start, end, weeks in phases:
        if start <= today <= end:
            cur_phase = (name, label, start, end)
            for w_name, w_start, w_end, w_desc in weeks:
                if w_start <= today <= w_end:
                    cur_week = w_name
                    week_desc = w_desc
                    break
            break

    total_phase = phases[-1][3] - phases[0][2]
    elapsed = today - phases[0][2]
    overall_pct = max(0, min(100, int(elapsed.days / total_phase.days * 100))) if total_phase.days else 0

    if cur_phase:
        title = f"{cur_phase[0]} ({cur_phase[1]}) — 시뮬 환경 셋업"
        count = f"{cur_week or '-'} {week_desc}"
        milestone = f"오늘: {today_date} · Phase 종료: {cur_phase[3].strftime('%m/%d')}"
    else:
        title = "Phase 미정"
        count = "-"
        milestone = ""

    return {
        "title": title,
        "count": count,
        "percent": overall_pct,
        "milestone": milestone,
    }


# =============================================================================
# 어제 커밋
# =============================================================================

TYPE_PATTERNS = [
    ("RESEARCH", ["research", "초안", "drafts", "🔬"]),
    ("SAMPLE", ["sample", "샘플", "🛠", "💻"]),
    ("LOG", ["로그", "log", "메트릭", "📊"]),
    ("DOCS", ["docs", "문서", "📝", "📋"]),
    ("FIX", ["fix", "버그", "🔧"]),
]

TYPE_CLASS = {
    "RESEARCH": "type-research",
    "SAMPLE": "type-sample",
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


def get_yesterday_commits():
    out, rc = run("git log --since='1 day ago' --pretty=format:'%s|||%H' -20")
    if rc != 0 or not out:
        return [], 0
    commits = []
    for line in out.split("\n"):
        if not line or "|||" not in line:
            continue
        msg, sha = line.split("|||", 1)
        msg = msg.strip()
        sha = sha.strip()[:7]
        # 변경된 파일 1~2개 추출
        files_out, _ = run(f"git show --name-only --pretty=format: {sha} | head -3")
        files = [f for f in files_out.split("\n") if f][:2]
        files_str = " · ".join(files) if files else ""
        commits.append({"msg": msg, "sha": sha, "files": files_str, "type": classify_commit(msg)})
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
# 시뮬 진척 (어제 research-log + research/simulation 신규)
# =============================================================================

def get_sim_progress_html(yesterday):
    log_path = REPO_ROOT / f"agent/research-log/{yesterday}.md"
    if not log_path.exists():
        return '<div class="no-issue">어제 시뮬 진척 기록 없음</div>'
    content = read_text(log_path)
    # 한줄 요약 추출
    summary = ""
    m = re.search(r"## 오늘 진행 단계\n+(.+?)(?=\n##|\Z)", content, re.DOTALL)
    phase_step = m.group(1).strip().split("\n")[0] if m else "Phase 진행 중"
    # 메트릭 추출
    m2 = re.search(r"## 실행 테스트 결과\n+(.+?)(?=\n##|\Z)", content, re.DOTALL)
    metrics = m2.group(1).strip() if m2 else ""

    return f'''<div class="research-summary">
      <div class="research-topic">{html_escape(phase_step)}</div>
      <div class="research-oneliner">상세 로그 → <code>agent/research-log/{yesterday}.md</code></div>
    </div>
    <div class="why-card">
      <pre style="margin:0;font-size:11px;color:#94a3b8;white-space:pre-wrap;font-family:monospace;">{html_escape(metrics[:400])}</pre>
    </div>'''


# =============================================================================
# 이슈 (어제 research-log의 "이슈" 섹션)
# =============================================================================

def get_issues_html(yesterday):
    log_path = REPO_ROOT / f"agent/research-log/{yesterday}.md"
    content = read_text(log_path)
    if not content:
        return '<div class="no-issue">현재 이슈 없음</div>'
    m = re.search(r"## 관찰 / 이슈\n+(.+?)(?=\n##|\Z)", content, re.DOTALL)
    if not m:
        return '<div class="no-issue">현재 이슈 없음</div>'
    issues_text = m.group(1).strip()
    if not issues_text or issues_text.startswith("(없음)"):
        return '<div class="no-issue">현재 이슈 없음</div>'
    items = []
    for line in issues_text.split("\n"):
        line = line.strip().lstrip("- ").strip()
        if line:
            items.append(f'<div class="issue-item">{html_escape(line)}</div>')
    return "\n    ".join(items) if items else '<div class="no-issue">현재 이슈 없음</div>'


# =============================================================================
# 외부 의존 / 결정 대기 (★ 핵심 ★)
# =============================================================================

def get_external_deps_html():
    deps = read_text(REPO_ROOT / "agent/external-dependencies.md")
    if not deps:
        return '<div class="no-issue">외부 의존 항목 없음</div>'
    # "진행중" 섹션의 [ ] 항목 추출
    m = re.search(r"## 🔴 진행중.+?(?=\n## |\Z)", deps, re.DOTALL)
    section = m.group(0) if m else deps
    items = []
    for match in re.finditer(r"-\s*\[\s*\]\s*(.+?)(?=\n-\s*\[|\n##|\Z)", section, re.DOTALL):
        body = match.group(1).strip()
        # 첫 줄: [담당] 제목
        first_line = body.split("\n", 1)[0].strip()
        title_html = html_escape(first_line[:120])
        # 마감일 추출
        deadline_m = re.search(r"마감[:\s]+(\d{4}-\d{2}-\d{2})", body)
        deadline = deadline_m.group(1) if deadline_m else ""
        items.append(f'''<div class="action-item">
      <span class="action-dot">📌</span>
      <span class="action-text">{title_html}{f' <span style="color:#f59e0b;font-size:11px;">(마감 {deadline})</span>' if deadline else ''}</span>
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
                topic = cols[1].split("—")[0].strip() if "—" in cols[1] else cols[1]
                desc = cols[1].split("—", 1)[1].strip() if "—" in cols[1] else ""
                items.append(f'<div class="pending-item"><div class="pending-dot"></div><span class="pending-label">{html_escape(topic)}</span><span class="pending-arrow">→</span><span class="pending-desc">{html_escape(desc)}</span></div>')
    return "\n      ".join(items) if items else '<div class="pending-item"><span class="pending-desc" style="color:#64748b;">결정 대기 항목 없음</span></div>'


# =============================================================================
# Phase 단계별 설명 (research/simulation/PHASE_ROADMAP.md 파싱)
# =============================================================================

def get_phase_details_html(today_date):
    today = datetime.datetime.strptime(today_date, "%Y-%m-%d").date()
    phase_info = get_phase_progress(today_date)

    # 단계별 핵심 내용
    if today.month == 5:
        steps = [
            ("01", "MuJoCo 3.x", "Apple Silicon 네이티브 패키지로 한 줄 설치, 환경변수 불필요"),
            ("02", "SO-ARM100/101 MJCF", "TheRobotStudio 공식 모델, 6-DoF 관절 + 그리퍼"),
            ("03", "viewer + Renderer", "macOS Metal 백엔드로 직접 시뮬 동작 검증"),
        ]
        topic = "Phase 0 — MuJoCo 시뮬 환경 셋업"
        oneliner = "MuJoCo + SO-ARM101 MJCF 모델로 시뮬레이션 환경을 구축하고, viewer로 6-DoF 동작을 검증합니다."
        why = "Mac Mini M5 단독으로 Phase 0~5(5~10월)를 진행하기 위한 환경. 실기 카메라 없이 시뮬 가상 카메라만 사용."
    elif today.month == 6:
        steps = [
            ("01", "200 에피소드 합성", "시뮬에서 자동 데이터 생성"),
            ("02", "ACT 사전학습", "epoch 100 학습, 손실 곡선 모니터링"),
            ("03", "실기 fine-tune", "5~10 에피소드로 실기 보정"),
        ]
        topic = "Phase 1 — 시뮬 데이터 + ACT 사전학습"
        oneliner = "시뮬 200 에피소드로 ACT 사전학습 → 실기 적은 데이터로 fine-tune합니다."
        why = "보고용 6월 계획(텔레오퍼레이션 검증)에 더해 실제로는 학습 단계 진입."
    else:
        steps = [("01", phase_info["title"], phase_info["count"])]
        topic = phase_info["title"]
        oneliner = phase_info["count"]
        why = "Phase별 상세는 PHASE_ROADMAP.md 참조."

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
        "header": "오늘의 시뮬 진척",
        "badge": "Phase 0",
        "topic": topic,
        "oneliner": oneliner,
        "steps_html": steps_html,
        "why": why,
    }


# =============================================================================
# 샘플/스크립트 현황
# =============================================================================

def get_samples_html():
    status_md = read_text(REPO_ROOT / "samples/SAMPLE_STATUS.md")
    items = []
    for m in re.finditer(r"^\s*[-*]\s*(test_[\w_]+\.py|sim_[\w_]+\.py)\s*[—:\-]\s*(.+?)$",
                         status_md, re.MULTILINE):
        name, desc = m.groups()
        items.append(f'<div class="sample-item"><span class="stars">⭐⭐</span><span class="sample-name">{html_escape(name)}</span><span class="sample-desc">{html_escape(desc.strip()[:60])}</span></div>')
    if not items:
        # find samples/ 디렉토리에서 .py 파일 직접 나열
        sim_dir = REPO_ROOT / "samples"
        if sim_dir.exists():
            for py in list(sim_dir.rglob("*.py"))[:5]:
                rel = py.relative_to(REPO_ROOT)
                items.append(f'<div class="sample-item"><span class="stars">⭐⭐</span><span class="sample-name">{html_escape(py.name)}</span><span class="sample-desc">{html_escape(str(rel.parent))}</span></div>')
    if not items:
        items = ['<div class="no-issue">샘플 스크립트 없음</div>']
    return "\n    ".join(items[:8])


def get_sample_review_html():
    return '''<div class="review-box">
      💡 모든 시뮬/학습 스크립트는 <code>.venv</code>에서 실행되어야 합니다. 시스템 Python 사용 시 <code>ModuleNotFoundError</code> 발생.<br/>
      실행: <code>source .venv/bin/activate &amp;&amp; python3 &lt;스크립트&gt;</code> 또는 <code>.venv/bin/python3 &lt;스크립트&gt;</code>
    </div>'''


# =============================================================================
# 경로 변경
# =============================================================================

def get_changes_html():
    out, _ = run("git log --since='1 day ago' --name-status --pretty=format:'---'")
    if not out:
        return '<div class="no-issue">변경 없음</div>'
    changes = {}  # path -> (add/move/del)
    for line in out.split("\n"):
        if not line or line == "---":
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0]
        path = parts[1]
        if status.startswith("A"):
            changes[path] = "add"
        elif status.startswith("D"):
            changes[path] = "del"
        elif status.startswith("R") or status.startswith("M") and path not in changes:
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
# 내일 예정
# =============================================================================

def get_tomorrow_html():
    return '''<div class="schedule-item"><span class="schedule-time">23:00</span><span class="schedule-tag tag-sample">시뮬 구축</span><span class="schedule-desc">PHASE_ROADMAP.md 다음 단계 자동 진행</span></div>
    <div class="schedule-item"><span class="schedule-time">23:30</span><span class="schedule-tag tag-research">테스트</span><span class="schedule-desc">시뮬 메트릭 수집 + research-log 작성</span></div>
    <div class="schedule-item"><span class="schedule-time">07:00</span><span class="schedule-tag tag-report">보고</span><span class="schedule-desc">일일 보고 메일 발송</span></div>'''


# =============================================================================
# 메일 발송
# =============================================================================

def send_email_smtp(recipient, subject, html_body):
    _load_smtp_env_from_hermes()
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
    phase_progress = get_phase_progress(header["today_date"])
    commits, count = get_yesterday_commits()
    phase_details = get_phase_details_html(header["today_date"])

    placeholders = {
        "<!--VOL_NUM-->": header["vol_num"],
        "<!--TODAY_DATE-->": header["today_date_full"],
        "<!--PHASE_TITLE-->": phase_progress["title"],
        "<!--PROGRESS_COUNT-->": phase_progress["count"],
        "<!--PROGRESS_PERCENT-->": str(phase_progress["percent"]),
        "<!--MILESTONE-->": phase_progress["milestone"],
        "<!--COMMITS_COUNT-->": f"{count}건",
        "<!--COMMITS_HTML-->": commits_to_html(commits),
        "<!--SIM_PROGRESS_HTML-->": get_sim_progress_html(header["yesterday"]),
        "<!--ISSUES_HTML-->": get_issues_html(header["yesterday"]),
        "<!--EXTERNAL_DEPS_HTML-->": get_external_deps_html(),
        "<!--PENDING_DECISIONS_HTML-->": get_pending_decisions_html(),
        "<!--PHASE_HEADER-->": phase_details["header"],
        "<!--PHASE_BADGE-->": phase_details["badge"],
        "<!--PHASE_TOPIC-->": phase_details["topic"],
        "<!--PHASE_ONELINER-->": phase_details["oneliner"],
        "<!--PHASE_STEPS_HTML-->": phase_details["steps_html"],
        "<!--PHASE_WHY-->": phase_details["why"],
        "<!--SAMPLES_HTML-->": get_samples_html(),
        "<!--SAMPLE_REVIEW_HTML-->": get_sample_review_html(),
        "<!--CHANGES_HTML-->": get_changes_html(),
        "<!--TOMORROW_HTML-->": get_tomorrow_html(),
    }

    html = template
    for k, v in placeholders.items():
        html = html.replace(k, v)
    return html, header


def main():
    _load_smtp_env_from_hermes()
    html, header = render_html()

    # 로컬 저장 (디버그/Obsidian용)
    out_dir = REPO_ROOT / "docs/01_overview/daily-reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{header['today_date']}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"[저장] {out_path}")

    # 수신자 결정
    test_mode = os.environ.get("EMAIL_TEST_MODE", "").lower() == "true"
    if test_mode:
        recipients = ["xaqwer@gmail.com"]
        print("[EMAIL_TEST_MODE=true] 본인(xaqwer)에게만 발송")
    else:
        recipients = [
            "xaqwer@gmail.com",
            "insoo.kum@hyundaielevator.com",
            "giheon.jang@hyundaielevator.com",
        ]
        print(f"[정상 발송] {len(recipients)}명에게 발송")

    subject = f"[CoP Physical AI] 일일 연구 보고 {header['vol_num']} | {header['today_date']}"

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
