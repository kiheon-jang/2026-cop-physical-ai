
import datetime
import json
import re
from hermes_tools import terminal, read_file, write_file

def get_today_info():
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))) # KST
    return {
        "today_date": today.strftime("%Y-%m-%d"),
        "today_weekday": ["월", "화", "수", "목", "금", "토", "일"][today.weekday()],
    }

def html_to_plaintext(html_content):
    plaintext = re.sub(r'<[^>]+>', '', html_content)
    plaintext = re.sub(r'\\s+', ' ', plaintext).strip()
    plaintext = plaintext.replace("&nbsp;", " ")
    plaintext = plaintext.replace("&amp;", "&")
    plaintext = plaintext.replace("&lt;", "<")
    plaintext = plaintext.replace("&gt;", ">")
    plaintext = plaintext.replace("&quot;", '\"')
    plaintext = plaintext.replace("&#39;", "'")
    return plaintext

def main(weekly_summary_content="<p>주간 요약 내용을 불러올 수 없습니다.</p>"):
    repo_path = "/Users/markmini/Documents/dev/2026-cop-physical-ai"
    obsidian_vault_path = "/Users/markmini/Documents/second-brain"

    today_info = get_today_info()

    html_body = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; padding: 20px; }}
            .container {{ max-width: 800px; margin: auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            h1 {{ color: #0056b3; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 20px; }}
            h2 {{ color: #0056b3; margin-top: 30px; border-bottom: 1px dashed #eee; padding-bottom: 5px; }}
            .date-section {{ background-color: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 15px; }}
            .date-header {{ font-weight: bold; color: #0056b3; margin-bottom: 5px; }}
            .summary-item {{ margin-left: 20px; margin-bottom: 5px; font-size: 0.9em; }}
            .footer {{ margin-top: 40px; text-align: center; font-size: 0.8em; color: #777; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>CoP Physical AI 주간 연구 요약 보고서 ({today_info['today_date']})</h1>
            <p>지난 한 주간 Hermes Agent가 수행한 주요 작업 요약입니다.</p>
            
            <h2>주간 작업 요약</h2>
            {weekly_summary_content}

            <div class="footer">
                이 보고서는 Hermes Agent에 의해 자동 생성되었습니다.
            </div>
        </div>
    </body>
    </html>
    '''
    
    report_dir_html = f"{repo_path}/docs/01_overview/weekly-reports"
    report_file_name_html = f"weekly-summary-{today_info['today_date']}.html"
    report_file_path_html = f"{report_dir_html}/{report_file_name_html}"
    write_file(path=report_file_path_html, content=html_body)
    print(f"HTML_REPORT_PATH:{report_file_path_html}")

    obsidian_report_dir = f"{obsidian_vault_path}/00_AI_Wiki/2026-cop-physical-ai/Weekly_Reports"
    obsidian_report_file_name = f"weekly-summary-{today_info['today_date']}.md"
    obsidian_report_file_path = f"{obsidian_report_dir}/{obsidian_report_file_name}"
    
    plaintext_content = html_to_plaintext(html_body)
    
    markdown_content = f"""---
tags: ["CoP/PhysicalAI", "WeeklyReport"]
date: {today_info['today_date']}
type: Weekly Report
status: generated
project: 2026-cop-physical-ai
---

# CoP Physical AI 주간 연구 요약 보고서 | {today_info['today_date']}

""" + plaintext_content

    write_file(path=obsidian_report_file_path, content=markdown_content)
    print(f"MARKDOWN_REPORT_PATH:{obsidian_report_file_path}")


if __name__ == "__main__":
    main()
