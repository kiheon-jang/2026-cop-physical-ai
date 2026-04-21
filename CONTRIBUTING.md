# 품질 기준 (CONTRIBUTING.md)

> 자동화 에이전트와 팀원 모두가 지켜야 할 품질 기준입니다.

---

## 📝 리서치 품질 기준

### 통과 기준 (latest-tech/ 이동 조건)
- [ ] 작성일 기준 **6개월 이내** 정보
- [ ] 핵심 개념 설명 포함 (초심자도 이해 가능한 수준)
- [ ] SO-ARM101 / LeRobot 프로젝트와의 연관성 명시
- [ ] 출처 링크 **1개 이상**
- [ ] 한 줄 요약 포함

### 파일명 규칙
```
research/drafts/YYYY-MM-DD_<주제-영문-kebab>.md
research/latest-tech/YYYY-MM-DD_<주제-영문-kebab>.md
```

### 갱신 주기
- `latest-tech/` 파일은 **6개월**마다 최신성 확인
- 오래된 내용은 상단에 `> ⚠️ DEPRECATED: YYYY-MM-DD 이후 내용 확인 필요` 표시

---

## 💻 샘플코드 완성도 기준

### 등급 정의

| 등급 | 기준 | SAMPLE_STATUS 표시 |
|------|------|-------------------|
| ⭐ 초안 | 구조만 있음, 실행 안 됨 | 🔄 작성중 |
| ⭐⭐ 기본 | 하드웨어 없이 실행됨, 핵심 테스트 PASS | ✅ 기본완성 |
| ⭐⭐⭐ 완성 | 전체 PASS, 주석 완비, 실사용 가능 | ✅ 완성 |

### ⭐⭐⭐ 완성 등급 체크리스트
- [ ] 하드웨어 없이 실행 시 전체 테스트 PASS
- [ ] 함수/클래스 docstring 작성
- [ ] lerobot 미설치 시 명확한 에러 메시지
- [ ] 실행 방법 주석 또는 README에 명시
- [ ] 마지막 검증 날짜 기록

### 파일명 규칙
```
samples/unit/test_<기능명>.py          # 단위 테스트
samples/hardware/run_<기능명>.py       # 하드웨어 실행
samples/training/test_<모델명>_training.py
samples/inference/test_<기능명>_inference.py
```

---

## 📬 커밋 메시지 규칙

| 타입 | 형식 | 예시 |
|------|------|------|
| 리서치 초안 | `🔬 [draft] <주제> — YYYY-MM-DD` | `🔬 [draft] ACT-benchmarks — 2026-04-22` |
| 리서치 확정 | `✅ [research] <주제> — YYYY-MM-DD` | `✅ [research] ACT-benchmarks — 2026-04-22` |
| 샘플코드 | `💻 [샘플] <설명> — YYYY-MM-DD` | `💻 [샘플] ACT 학습 파이프라인 — 2026-04-22` |
| 문서 | `📝 [docs] <설명>` | `📝 [docs] 데이터 수집 가이드 업데이트` |
| 주간 검수 | `🔄 [주간검수] YYYY-MM-DD 주간 정리` | |
| 결정 로그 | `🗂️ [결정] <주제> <채택/기각>` | `🗂️ [결정] ACT 채택` |
| AGENT_PROCESS 업데이트 | `🤖 [agent] AGENT_PROCESS.md 업데이트` | |
