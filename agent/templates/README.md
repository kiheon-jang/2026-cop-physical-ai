# 템플릿 파일 안내 (Templates)

이 프로젝트에서 사용하는 HTML 템플릿 파일 경로입니다.

---

## 일일 보고 메일 템플릿

**파일**: `../docs/01_overview/mail-template.html`  
**퍼블릭 미리보기**: https://ookixght.gensparkclaw.com/mail-preview.html  
**서버 경로**: `/var/www/html/mail-preview.html`

### 교체 필요 항목 (매일 크론에서)

| 플레이스홀더 | 교체 내용 |
|-------------|----------|
| `Vol.XXX` | Vol 번호 (시작일 2026-04-21 기준 D+N) |
| `YYYY-MM-DD (요일)` | 오늘 KST 날짜 |
| `[1] 어제 완료한 작업` | GitHub 커밋 목록 |
| `[3] 데이터 수집 현황` | TRACKING.md 수치 |
| `[5] 오늘의 기술 리서치` | research/drafts/ 신규 파일 |
| `[6] 샘플코드 현황` | SAMPLE_STATUS.md |
| `[7] 경로 및 구조 변경` | 오늘 커밋 파일 변경 |
| `[8] 내일 예정` | 크론 스케줄 기준 내일 예정 |

---

## 기술 결정 폼

**파일**: `../docs/01_overview/decisions-form.html`  
**퍼블릭 URL**: https://ookixght.gensparkclaw.com/decisions.html  
**서버 경로**: `/var/www/html/decisions.html`

### 동작 방식

1. 팀원이 URL에서 항목 선택 + 이유 입력
2. GitHub Personal Access Token 입력 (최초 1회, localStorage 저장)
3. 제출 시 `research/decisions/YYYY-MM-DD_항목.md` 자동 생성
4. 다음 보고서부터 ✅ 결정완료 표시

### 정적 파일 업데이트 방법

```bash
# 템플릿 수정 후 서버에 반영
sudo cp docs/01_overview/mail-template.html /var/www/html/mail-preview.html
sudo cp docs/01_overview/decisions-form.html /var/www/html/decisions.html
```
