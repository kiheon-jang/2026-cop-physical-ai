# 보고용 증거 인덱스 — 2026-10

10월 = 기준선 동결(학습·측정·판정·환경 불변). 신규 측정 산출물 없음.

- **RS232 파지 타이밍 측정가능성** (2026-10-03) — 기존 덤프로는 파지 타이밍 어긋남 측정 불가
  (판별 변수 = 접촉, 덤프에는 qpos 만; 집게각 대리값 간격 0.020 rad → 판별 불가). 계측 한 줄
  이관 처방. → 월간 보고 잔여 결함/후속과제 섹션.
  근거: `agent/research-log/2026-10-03.md`, `research/simulation/2026-10-03_rs232-pinch-timing-measurability.md`
- **동결 무결성 검증(10-08)** (2026-10-08) — 환경 불변 근거: episodes_rs232 100ep/16093f · 모델 락
  `act_rs232_sim/epoch_0041` mtime Sep 18·335,947,896 B · 마커 정합 · rollout 0.600 · MuJoCo 3.8.0 render OK.
  → 월간 보고 "환경 불변" / 시연 재현성 섹션.
  근거: `agent/research-log/2026-10-08.md`, `research/simulation/2026-10-08_oct-freeze-hold.md`
- **동결 무결성 검증(10-10)** (2026-10-10) — 환경 불변 연속성: 동일 지표 전수 일치(episodes 100/16093 ·
  ckpt 335,947,896 B mtime Sep 18 · 마커 정합 · rollout 0.600/9.66mm · render OK 36.7ms/frame). 회귀 0.
  → 월간 보고 "환경 불변" / 시연 재현성 섹션.
  근거: `agent/research-log/2026-10-10.md`, `research/simulation/2026-10-10_oct-freeze-integrity-verify.md`
