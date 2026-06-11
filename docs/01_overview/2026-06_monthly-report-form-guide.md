# 월간 활동보고서 폼 양식 작성 가이드 (FORM)

> 대시보드의 "보고용 자료" 메뉴는 활동보고서를 **5섹션 폼 양식** 으로 렌더링합니다.
> 매월 보고서를 작성할 때 아래 가이드대로 작성하면 자동으로 폼 양식 + 마크다운 원문 양쪽 모두 노출됩니다.

대시보드: https://cop-physical-ai.hermesmark.site/ → 보고용 자료

---

## 1. 파일 위치 + 파일명

```
~/Documents/second-brain/03 Areas/회사문서/CoP_PhysicalAI/CoP_PhysicalAI_YYYY-MM_활동보고서.md
```

예: `CoP_PhysicalAI_2026-06_활동보고서.md`

같은 월에 여러 파일이 있으면 `mtime` 최신 1건만 대시보드에 노출.

---

## 2. 파일 구조

YAML frontmatter (`---` 사이) + 마크다운 본문. **frontmatter 데이터로 폼 양식이 자동 렌더**됨.

```markdown
---
month: 2026-06
title: 2026 CoP Physical AI — 첫걸음
subtitle: Physical AI ...
period: 2026.06.01 ~ 2026.06.30
report_round: 제3회차
status_label: 진행중
overview:
  cop_name: 2026 CoP Physical AI — 첫걸음
  activity_topic: SO-ARM101 기반 모방학습·강화학습 로보틱스 기술 내재화
  final_goal: PCB 제품 조정 자동화 및 RS232 포트 HHT 자동 결선 시연 (10월)
status:
  state: Phase 1(사전학습) 완료
  progress_pct: 75
  progress_weeks: 12/16주
  detail: 데이터 200ep 합성 완료, ACT 학습 6/15 착수, epoch 50 진행 중.
achievements:
  - { title: 데이터 합성, value: "200ep / 12,400 frames 완료" }
  - { title: ACT 학습 진척, value: "epoch 50 / loss 0.023" }
  - { title: 정기 미팅, value: "2회 진행" }
activity_summary: 200 에피소드 데이터셋 합성 완료 후, ACT 학습 파이프라인 구축 및 학습 착수를 중심으로 Phase 1 사전학습 단계를 완료하였음.
weeks:
  - { week: 1주차, date: 06.01 ~ 06.07, content: 시뮬 데이터 합성 환경 점검 · LeRobot Dataset v3.0 포맷 검증 }
  - { week: 2주차, date: 06.08 ~ 06.14, content: train_act.py 구현 · load_dataset / build_model / train 함수 작성 }
  - { week: 3주차, date: 06.15 ~ 06.21, content: ACT 학습 착수 (Phase 1 W3) · epoch 1~30 진행 }
  - { week: 4주차, date: 06.22 ~ 06.30, content: epoch 30~50 진행 · 메트릭 검증 · 7월 실기 검증 준비 }
next_month:
  title: 7월 계획
  period: 2026.07.01 ~ 2026.07.31
  categories:
    - label: 실기 검증 (Sim2Real)
      state: 예정
      items:
        - { title: 시뮬 모델 실기 이식, desc: "outputs/train/.../last 체크포인트 → 실기 로봇팔 적재" }
        - { title: 실기 50ep 데이터 수집, desc: "텔레오퍼레이션 또는 학습된 모델 추론으로 실기 데이터 합성" }
        - { title: 시뮬 vs 실기 메트릭 비교, desc: "Sim2Real gap 측정 + Domain Randomization 적용" }
    - label: 학습 및 연구 활동
      state: 진행중
      items:
        - { title: ACT 학습 메트릭 분석, desc: "loss curve 분석, 과적합 여부 점검" }
        - { title: 다음 단계 준비, desc: "Phase 3 PCB 부품 픽업 시나리오 설계" }
site_caption: ACT 학습 시작 및 데이터셋 합성 환경
site_image:
---

# 2026년 사내 CoP 활동보고서 — 6월

(마크다운 본문 — 폼 양식 외에 원문 토글로 노출되는 부분)
```

---

## 3. frontmatter 필드 상세

### 헤더 (필수)
| 필드 | 설명 | 예 |
|------|------|-----|
| `month` | YYYY-MM | `2026-06` |
| `title` | CoP 명칭 | `2026 CoP Physical AI — 첫걸음` |
| `period` | 보고 기간 | `2026.06.01 ~ 2026.06.30` |
| `report_round` | 보고 회차 | `제3회차` |
| `status_label` | 상태 라벨 | `진행중` / `완료` / `예정` |

### overview (CoP 개요 표)
| 필드 | 설명 |
|------|------|
| `cop_name` | CoP 풀 명칭 |
| `activity_topic` | 활동 주제 |
| `final_goal` | 최종 목표 (10월) |

### status (활동 현황 박스)
| 필드 | 설명 |
|------|------|
| `state` | 현재 단계 한 줄 |
| `progress_pct` | 진행률 % (숫자) |
| `progress_weeks` | "N/16주" 형식 |
| `detail` | 상세 설명 |

### achievements (주요 성과 카드)
리스트, 각 항목 `{ title, value }`. **콤마/괄호 있는 value 는 쌍따옴표 필수**:
```yaml
- { title: 데이터 합성, value: "200ep / 12,400 frames 완료" }
```

### activity_summary (활동 요약)
긴 한 문장. 콤마 있으면 쌍따옴표 권장.

### weeks (주차별 활동 표)
리스트, 각 항목 `{ week, date, content }`. content 에 콤마 있으면 쌍따옴표.

### next_month (차월 계획)
```yaml
next_month:
  title: 7월 계획
  period: 2026.07.01 ~ 2026.07.31
  categories:
    - label: 카테고리명
      state: 예정    # 또는 진행중, 완료
      items:
        - { title: 항목명, desc: "설명 (콤마 있으면 쌍따옴표)" }
```

### 활동 현장 사진
| 필드 | 설명 |
|------|------|
| `site_caption` | 사진 캡션 |
| `site_image` | 이미지 경로 (비워두면 placeholder) |

---

## 4. 사진 추가 방법

1. 이미지 파일 준비 (jpg/png/webp)
2. Obsidian 폴더 또는 사내 공유 위치에 업로드
3. frontmatter `site_image:` 에 절대 URL 또는 상대 경로 입력
4. cron 자동 갱신 (다음 23:30) 또는 수동으로 `build.py --json` 실행

placeholder 상태로도 폼 자체는 노출되니, 사진 없어도 보고서 발행 가능.

---

## 5. YAML 작성 주의사항

1. **콤마(,) 포함 값은 쌍따옴표** — YAML inline dict 의 콤마는 separator
   - ❌ `value: 200ep, 12400 frames`  → "200ep" 만 인식
   - ✅ `value: "200ep, 12400 frames"`

2. **콜론(:) 포함 값도 쌍따옴표**
   - ❌ `value: 6월: 데이터 합성`
   - ✅ `value: "6월: 데이터 합성"`

3. **들여쓰기는 스페이스 2칸** (탭 X)

4. **`date: 2026-06-27` 같은 ISO 날짜는 자동으로 datetime 으로 변환**
   - 단, JSON 직렬화에서 string 으로 다시 변환됨 (안전)

---

## 6. 자동 반영 흐름

1. Obsidian 폴더에 `.md` 저장
2. 매일 23:30 cron 끝에 `build.py --json` 자동 실행
3. `data.json` 의 `monthly_reports[].form` 필드에 emit
4. chokidar 가 변경 감지 → WebSocket 푸시
5. 브라우저에서 자동 갱신 (새로고침 X)

수동 즉시 반영 시:
```bash
cd /Volumes/MARK_DATA/dev/2026-cop-physical-ai
python3 dashboard/build.py --json
```

---

## 7. 폼 ↔ 원문 토글

폼 양식 데이터가 있으면 보고서 본문 상단에 토글 버튼 자동 노출:
- **📋 폼 양식** — frontmatter 기반 5섹션 폼
- **📝 원문 (마크다운)** — 마크다운 본문 풀 렌더

폼 데이터가 부족하면 (frontmatter 없거나 status/weeks/achievements 모두 비어있음) 토글 안 보이고 마크다운만 노출.

---

## 8. 5섹션 폼 양식 구조 (pptx 매핑)

| 슬라이드 (참고 pptx) | 폼 섹션 | 데이터 |
|---|---|---|
| 1 | 표지 + 활동현황 + 주요 성과 | `title`, `period`, `report_round`, `status`, `achievements` |
| 2 | CoP 개요 표 | `overview.*` + `period` + `report_round` |
| 3 | N월 활동 및 성과 | `activity_summary`, `overview.final_goal`, `weeks` |
| 4 | 차월 계획 | `next_month.*` |
| 5 | 활동 현장 사진 | `site_caption`, `site_image` (placeholder 가능) |

---

## 9. 4월/5월 보고서 = 표준 양식

이미 작성된 4월/5월 보고서가 표준 frontmatter 예시입니다. 다음 달 작성 시 그대로 복사 + month/period/내용만 교체.

```
~/Documents/second-brain/03 Areas/회사문서/CoP_PhysicalAI/CoP_PhysicalAI_2026-04_활동보고서.md
~/Documents/second-brain/03 Areas/회사문서/CoP_PhysicalAI/CoP_PhysicalAI_2026-05_활동보고서.md
```
