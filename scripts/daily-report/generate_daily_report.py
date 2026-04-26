
import datetime
import json
import re
from hermes_tools import terminal, read_file, send_message, write_file

def get_today_info():
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))) # KST
    start_date = datetime.datetime(2026, 4, 21, 0, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=9)))
    
    delta = today - start_date
    vol_num = delta.days + 1
    
    days = ["월", "화", "수", "목", "금", "토", "일"]
    today_weekday = days[today.weekday()]
    
    return {
        "today_date": today.strftime("%Y-%m-%d"),
        "today_weekday": today_weekday,
        "vol_num": f"Vol.{vol_num:03d}"
    }

def get_github_commits(repo_path, count=10):
    # gh auth token을 사용하여 git remote 설정
    terminal(command=f"git -C {repo_path} remote set-url origin https://$(gh auth token)@github.com/kiheon-jang/2026-cop-physical-ai.git")
    
    # 어제 커밋 이력 가져오기
    result = terminal(command=f"git -C {repo_path} log --since='yesterday' --pretty=format:'%s' -{count}")
    if result["exit_code"] == 0 and result["output"]:
        return result["output"].strip().split('\\n')
    return []

def get_file_content(file_path):
    result = read_file(path=file_path)
    if result and result.get("content"):
        return result["content"]
    return ""

def format_commits_to_html(commits):
    if not commits:
        return "<div class=\\"no-issue\\">어제 작업 없음</div>", "0건"
    
    html_items = []
    task_num = 1
    for commit in commits:
        match = re.match(r'\[(.*?)\] (.*?) — (.*)', commit)
        if match:
            task_type_raw, task_title, _ = match.groups()
            task_type = "DOCS"
            if "research" in task_type_raw.lower() or "초안" in task_type_raw:
                task_type = "RESEARCH"
            elif "sample" in task_type_raw.lower() or "샘플" in task_type_raw:
                task_type = "SAMPLE"
            
            html_items.append(f'''
            <div class="task-item">
              <div class="task-num">{task_num}</div>
              <div class="task-content">
                <div><span class="task-type type-{task_type.lower()}">{task_type}</span><span class="task-title">{task_title}</span></div>
                <div class="task-path"></div> <!-- Commit message doesn't contain paths directly, so leave empty -->
              </div>
            </div>
            ''')
            task_num += 1
    return "\\n".join(html_items), f"{len(commits)}건"

def parse_data_collection_status(tracking_content):
    match = re.search(r'현재: (\d+) / (\d+) 에피소드', tracking_content)
    if match:
        current, total = int(match.group(1)), int(match.group(2))
        progress_percent = (current / total) * 100 if total > 0 else 0
        return current, total, f"{progress_percent:.0f}%"
    return 0, 50, "0%" # Default values

def parse_research_draft(repo_path, today_date):
    draft_path = f"{repo_path}/research/drafts/"
    # 오늘 날짜에 해당하는 리서치 초안 파일 찾기
    result = terminal(command=f"ls {draft_path} | grep {today_date}")
    if result["exit_code"] == 0 and result["output"]:
        file_name = result["output"].strip().split('\\n')[0]
        content = get_file_content(f"{draft_path}/{file_name}")
        
        topic_match = re.search(r'# (.*)', content)
        oneliner_match = re.search(r'## 💡 한 줄 요약\\n(.*?)\\n', content, re.DOTALL)
        concepts_match = re.findall(r'(\d+)\. \[(.*?)\].*?: (.*?)\\n', content)
        why_match = re.search(r'## 📊 왜 우리 프로젝트에 중요한가\\n(.*?)\\n', content, re.DOTALL)
        
        topic = topic_match.group(1).strip() if topic_match else "N/A"
        oneliner = oneliner_match.group(1).strip() if oneliner_match else "N/A"
        why = why_match.group(1).strip() if why_match else "N/A"

        concept_html = ""
        for num, name, desc in concepts_match:
            concept_html += f'''
            <div class="concept-item">
              <div class="concept-num">{num}</div>
              <div>
                <div class="concept-name">{name}</div>
                <div class="concept-desc">{desc}</div>
              </div>
            </div>
            '''
        
        return {
            "exists": True,
            "topic": topic,
            "oneliner": oneliner,
            "concepts": concept_html,
            "why": why,
            "read_more_link": f"https://github.com/kiheon-jang/2026-cop-physical-ai/blob/main/research/drafts/{file_name}"
        }
    return {"exists": False}

def parse_sample_status(sample_status_content):
    lines = sample_status_content.strip().split('\\n')
    html_items = []
    review_box_content = "" # Assuming review box content is not dynamically generated for now

    for line in lines[1:]: # Skip header
        parts = line.split('|')
        if len(parts) >= 4:
            status = parts[1].strip()
            name = parts[2].strip()
            desc = parts[3].strip()

            stars = ""
            if "⭐⭐⭐" in status: stars = "⭐⭐⭐"
            elif "⭐⭐" in status: stars = "⭐⭐"
            elif "⭐" in status: stars = "⭐"

            html_items.append(f'''
            <div class="sample-item"><span class="stars">{stars}</span><span class="sample-name">{name}</span><span class="sample-desc">{desc}</span></div>
            ''')
    return "\\n".join(html_items), review_box_content # Review box not implemented

def parse_decisions(decisions_content):
    lines = decisions_content.strip().split('\\n')
    pending_items = []
    
    for line in lines[1:]: # Skip header
        parts = line.split('|')
        if len(parts) >= 4:
            status = parts[1].strip()
            item_name = parts[2].strip()
            item_desc = parts[3].strip()

            if "⏳ 대기" in status:
                pending_items.append(f'''
                <div class="pending-item"><div class="pending-dot"></div><span class="pending-label">{item_name}</span><span class="pending-arrow">→</span><span class="pending-desc">{item_desc}</span></div>
                ''')
            elif "✅ 결정완료" in status:
                # If a decision is made, we can choose to remove it from pending or mark it.
                pass # For now, only show pending in the pending section

    return "\\n".join(pending_items)

def get_path_changes(repo_path):
    # 어제 이후의 파일 변경사항 가져오기
    result = terminal(command=f"git -C {repo_path} diff --name-status --since='yesterday'")
    if result["exit_code"] == 0 and result["output"]:
        lines = result["output"].strip().split('\\n')
        html_changes = []
        for line in lines:
            if line:
                status, path = line.split('\\t', 1)
                change_type = ""
                type_class = ""
                if status == "A":
                    change_type = "ADD"
                    type_class = "type-add"
                elif status.startswith("R"): # Renamed
                    change_type = "MOVE"
                    type_class = "type-move"
                elif status == "D":
                    change_type = "DEL"
                    type_class = "type-del"
                elif status == "M":
                    change_type = "MOD"
                    type_class = "type-mod" # No specific style for MOD yet

                if change_type:
                    html_changes.append(f'''
                    <div class="change-item"><span class="change-type {type_class}">{change_type}</span><span class="change-path">{path}</span></div>
                    ''')
        return "\\n".join(html_changes)
    return "<div class=\\"no-issue\\">변경 없음</div>"

def get_next_day_cron_schedule(today_weekday_kor):
    cron_jobs = [
        {"time": "23:00", "tag": "RESEARCH", "desc": "ACT vs Diffusion Policy vs π0 최신 벤치마크 비교", "day": "월"},
        {"time": "23:00", "tag": "RESEARCH", "desc": "Isaac Lab / Isaac Sim 강화학습 최신 동향", "day": "화"},
        {"time": "23:00", "tag": "RESEARCH", "desc": "Sim2Real 격차 해소 최신 기법", "day": "수"},
        {"time": "23:00", "tag": "RESEARCH", "desc": "VLA(Vision-Language-Action) 모델 최신 논문", "day": "목"},
        {"time": "23:00", "tag": "RESEARCH", "desc": "모방학습 데이터 효율화 기법", "day": "금"},
        {"time": "23:00", "tag": "RESEARCH", "desc": "LeRobot 커뮤니티 최신 업데이트", "day": "토"},
        {"time": "23:00", "tag": "RESEARCH", "desc": "경쟁사/유사 프로젝트 동향 (SO-ARM, LeKiwi, XLeRobot)", "day": "일"},
        
        {"time": "23:30", "tag": "SAMPLE", "desc": "training/test_act_training.py", "day": "월"},
        {"time": "23:30", "tag": "SAMPLE", "desc": "training/test_diffusion_training.py", "day": "화"},
        {"time": "23:30", "tag": "SAMPLE", "desc": "inference/test_inference_pipeline.py", "day": "수"},
        {"time": "23:30", "tag": "SAMPLE", "desc": "data-collection/test_episode_quality.py", "day": "목"},
        {"time": "23:30", "tag": "SAMPLE", "desc": "motor-control/test_torque_limit.py", "day": "금"},
        {"time": "23:30", "tag": "SAMPLE", "desc": "training/test_hyperparameter_search.py", "day": "토"},
        {"time": "23:30", "tag": "SAMPLE", "desc": "inference/test_camera_pipeline.py", "day": "일"},

        {"time": "07:00", "tag": "REPORT", "desc": "일일 보고 메일 발송", "day": "월"},
        {"time": "07:00", "tag": "REPORT", "desc": "일일 보고 메일 발송", "day": "화"},
        {"time": "07:00", "tag": "REPORT", "desc": "일일 보고 메일 발송", "day": "수"},
        {"time": "07:00", "tag": "REPORT", "desc": "일일 보고 메일 발송", "day": "목"},
        {"time": "07:00", "tag": "REPORT", "desc": "일일 보고 메일 발송", "day": "금"},
        {"time": "07:00", "tag": "REPORT", "desc": "일일 보고 메일 발송", "day": "토"},
        {"time": "07:00", "tag": "REPORT", "desc": "일일 보고 메일 발송", "day": "일"},

        {"time": "22:00", "tag": "REVIEW", "desc": "주간 검수 + 최신화", "day": "일"}
    ]
    
    tomorrow_weekday_idx = (datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).weekday() + 1) % 7
    tomorrow_weekday_kor = days[tomorrow_weekday_idx]
    
    tomorrow_schedule = [job for job in cron_jobs if job["day"] == tomorrow_weekday_kor]
    
    if not tomorrow_schedule:
        return "<div class=\\"no-issue\\">내일 예정된 작업 없음</div>"
    
    html_items = []
    for item in tomorrow_schedule:
        html_items.append(f'''
        <div class="schedule-item"><span class="schedule-time">{item["time"]}</span><span class="schedule-tag tag-{item["tag"].lower()}">{item["tag"]}</span><span class="schedule-desc">{item["desc"]}</span></div>
        ''')
    return "\\n".join(html_items)


def main():
    repo_path = "/Users/markmini/Documents/dev/2026-cop-physical-ai"

    # 1. 오늘 날짜, 요일, Vol 번호 계산
    today_info = get_today_info()
    
    # 2. 어제 커밋 이력 가져오기
    commits = get_github_commits(repo_path)
    formatted_commits, commit_count_str = format_commits_to_html(commits)

    # 3. 데이터 수집 현황
    tracking_content = get_file_content(f"{repo_path}/docs/05_data-collection/TRACKING.md")
    current_eps, total_eps, progress_percent = parse_data_collection_status(tracking_content)

    # 4. 결정 대기 항목
    decisions_content = get_file_content(f"{repo_path}/research/decisions/README.md")
    pending_decisions_html = parse_decisions(decisions_content)

    # 5. 오늘 리서치 초안
    research_draft = parse_research_draft(repo_path, today_info["today_date"])
    
    research_section_html = ""
    if research_draft["exists"]:
        research_section_html = f'''
        <div class="section">
            <div class="section-header">
            <span class="section-icon">🔬</span>
            <span class="section-title">오늘의 기술 리서치</span>
            <span class="section-badge">초안</span>
            </div>
            <div class="research-summary">
            <div class="research-topic">{research_draft["topic"]}</div>
            <div class="research-oneliner">{research_draft["oneliner"]}</div>
            </div>
            <div class="concept-list">
                {research_draft["concepts"]}
            </div>
            <div class="why-card">
            우리 프로젝트에서 왜 중요한가: {research_draft["why"]}
            </div>
            <div class="read-more">더 읽어보기: <a href="{research_draft["read_more_link"]}">research/drafts →</a></div>
        </div>
        '''
    else:
        research_section_html = '''
        <div class="section">
            <div class="section-header">
            <span class="section-icon">🔬</span>
            <span class="section-title">오늘의 기술 리서치</span>
            <span class="section-badge">초안</span>
            </div>
            <div class="no-issue">오늘 리서치 결과 없음</div>
        </div>
        '''

    # 6. 샘플코드 현황
    sample_status_content = get_file_content(f"{repo_path}/samples/SAMPLE_STATUS.md")
    samples_html, _ = parse_sample_status(sample_status_content)
    # Review box placeholder for now
    sample_review_box_html = '''
    <div class="review-box">
        💡 코드 리뷰 포인트: `test_follower_basic.py`는 하드웨어 없이 실행 가능한 단위테스트 구조를 보여줍니다. `dataclass`로 설정을 분리하고, 실제 실행 코드를 `if __name__ == "__main__"` 하단에 주석 처리한 패턴은 팀 전체가 사용할 수 있습니다.
    </div>
    '''

    # 7. 경로 및 구조 변경사항
    path_changes_html = get_path_changes(repo_path)

    # 8. 내일 예정
    next_day_schedule_html = get_next_day_cron_schedule(today_info["today_weekday"])
    
    # HTML 템플릿 로드
    html_template = get_file_content(f"{repo_path}/docs/01_overview/mail-template.html")

    # 플레이스홀더 교체
    html_body = html_template.replace("Vol.002", today_info["vol_num"])
    html_body = html_body.replace("2026-04-22 (수)", f"{today_info['today_date']} ({today_info['today_weekday']})")
    
    # 데이터 수집 진행 현황
    html_body = html_body.replace('<span class=\\"progress-count\\">0 / 50</span>', f'<span class=\\"progress-count\\">{current_eps} / {total_eps}</span>')
    html_body = html_body.replace('style=\\"width: 0%\\"', f'style=\\"width: {progress_percent}\\"')

    # 어제 완료한 작업
    html_body = re.sub(r'<!-- 1\. 어제 완료 작업 -->.*?<div class=\\"section-badge\\">.*?건</div>.*?<div class=\\"task-item\\">.*?</div>.*?</div>\\s*</div>', 
                       f'''<!-- 1. 어제 완료 작업 -->
  <div class=\\"section\\">
    <div class=\\"section-header\\">
      <span class=\\"section-icon\\">✅</span>
      <span class=\\"section-title\\">어제 완료한 작업</span>
      <span class=\\"section-badge\\">{commit_count_str}</span>
    </div>
    {formatted_commits}
  </div>''', html_body, flags=re.DOTALL)
    
    # 이슈/문제점 (현재 이슈가 없으므로 고정된 내용 사용)
    html_body = re.sub(r'<!-- 2\. 이슈 -->.*?</div>\\s*</div>', 
                       '''<!-- 2. 이슈 -->
  <div class=\\"section\\">
    <div class=\\"section-header\\">
      <span class=\\"section-icon\\">🔴</span>
      <span class=\\"section-title\\">이슈 / 문제점</span>
    </div>
    <div class=\\"no-issue\\">현재 보고된 주요 이슈 없음</div>
  </div>''', html_body, flags=re.DOTALL)

    # 팀 요청사항 (결정 대기 항목)
    html_body = re.sub(r'<div class=\\"pending-section\\">.*?<a href=\\"https://ookixght.gensparkclaw.com/decisions\\".*?</div>', 
                       f'''<div class="pending-section">
      <div class="pending-title">⏳ 결정 대기 항목</div>
        {pending_decisions_html}
      <div class="decision-btn-wrap">
        <a href="https://ookixght.gensparkclaw.com/decisions.html" class="decision-btn">🗂️ 결정 폼 열기 — 여기서 직접 결정하세요 →</a>
        <div class="decision-hint">결정 후 다음 보고서부터 ✅ 결정완료로 자동 표시됩니다</div>
      </div>
    </div>''', html_body, flags=re.DOTALL)

    # 오늘의 기술 리서치
    html_body = re.sub(r'<!-- 4\. 리서치 -->.*?</div>\\s*</div>', 
                       f'''<!-- 4. 리서치 -->
{research_section_html}''', html_body, flags=re.DOTALL)

    # 샘플코드 현황
    html_body = re.sub(r'<!-- 5\. 샘플코드 -->.*?</div>\\s*</div>', 
                       f'''<!-- 5. 샘플코드 -->
  <div class=\\"section\\">
    <div class=\\"section-header\\">
      <span class=\\"section-icon\\">💻</span>
      <span class=\\"section-title\\">샘플코드 현황</span>
    </div>
    {samples_html}
    {sample_review_box_html}
  </div>''', html_body, flags=re.DOTALL)

    # 경로 및 구조 변경
    html_body = re.sub(r'<!-- 6\. 경로 변경 -->.*?</div>\\s*</div>', 
                       f'''<!-- 6. 경로 변경 -->
  <div class=\\"section\\">
    <div class=\\"section-header\\}>
      <span class=\\"section-icon\\">📁</span>
      <span class=\\"section-title\\">경로 및 구조 변경</span>
    </div>
    {path_changes_html}
  </div>''', html_body, flags=re.DOTALL)

    # 내일 예정
    html_body = re.sub(r'<!-- 7\. 내일 예정 -->.*?</div>\\s*</div>', 
                       f'''<!-- 7. 내일 예정 -->
  <div class=\\"section\\">
    <div class=\\"section-header\\}>
      <span class=\\"section-icon\\">📅</span>
      <span class=\\"section-title\\">내일 예정</span>
    </div>
    {next_day_schedule_html}
  </div>''', html_body, flags=re.DOTALL)
    
    # 메일 내용 파일로 저장
    report_dir = f"{repo_path}/docs/01_overview/daily-reports"
    report_file_path = f"{report_dir}/{today_info['today_date']}.html"
    write_file(path=report_file_path, content=html_body)
    print(f"Daily report saved to {report_file_path}")

    # 이메일 발송
    recipients = ["xaqwer@gmail.com", "insoo.kum@hyundaielevator.com", "giheon.jang@hyundaielevator.com"]
    subject = f"[CoP Physical AI] 일일 연구 보고 {today_info['vol_num']} | {today_info['today_date']}"

    success_count = 0
    for recipient in recipients:
        print(f"Sending email to {recipient}...")
        send_result = send_message(target=recipient, message=html_body) # HTML content
        if send_result and send_result.get("success"):
            print(f"Successfully sent to {recipient}")
            success_count += 1
        else:
            print(f"Failed to send to {recipient}: {send_result.get('error', 'Unknown error')}")
    
    print(f"Email sending complete. {success_count}/{len(recipients)} successful.")

if __name__ == "__main__":
    main()
