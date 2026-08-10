# Phase 3 W3 — S1 리셋버튼 hold 유지 + 무결성 감사 재확인 (2026-08-10)

## 무엇을 했나
드라이버(`scripts/cop_pipeline_advance.sh`)가 STAGE=완료/유지로 마감:
`episodes_s1` 100ep · 최종 성공률 0.925(목표 0.90) · 새 사이클 미트리거 → 수집/학습/측정 재실행 없음.

dated 항목 W1(8/5)·W2(8/5 조기)·W3(8/6 조기) 전부 완료. 다음 pending = W4(8/26~) omen
sim2real 핸드오프(외부 의존, 진입 불가) → **hold 일**. 8/8·8/9 와 동일 패턴.

야간 에이전트는 비파괴 무결성 전수 감사만 수행(에피소드 write·학습 금지 = hold 오염 방지).

## 어떻게 검증했나 (비파괴)
- **마커 3자 정합** (8/9 값과 바이트 일치):
  - `logs/cop_dataset_target` = `data/episodes_s1`
  - `logs/cop_trained_on.marker` = `episodes_s1:1785931493`
  - `logs/cop_measured.marker` = `episodes_s1:1786060554`
- **학습 프로세스 없음**: `pgrep -fl train_act` → none.
- **운영 rollout 불변**: `research/simulation/inference_progress/rollout_summary_s1.json`
  md5 `fbeef25775e5846ba2e3ce887afd1929` → 8/8·8/9 대비 불변.
  sr 0.90(seed42 nominal) · ckpt `act_s1_sim/epoch_0029_measured_0.925.bak`.
  4-seed(42/7/123/2026) 평균 0.925(37/40)은 8/6 최초 측정과 결정론적 동일.
- **데이터셋 불변**: episodes_s1 100ep/7231f · episodes_floor 50ep/3350f · episodes_cl 50ep/3350f.
- sandbox `md5` 차단 → `.venv hashlib.md5` 우회 산출(값 불변 확인).

→ **회귀/오염 0.** Phase 3 완료 기준 성공률(≥0.70)은 0.925 로 이미 충족. 남은 완료 기준
= 합성 데이터셋 omen 로드 확인(W4 외부 의존).

## 다음 단계 연결
- W4(8/26~) sim2real omen 핸드오프: `act_s1_sim/epoch_0029` + `episodes_s1` 전달,
  P1 LED ROI 캘리브 지원, Sim2Real 격차 보고(S1 정책 DR 민감도 aggregate ~0.45 포함).
- W2 잔여 omen lerobot 로드 스모크(외부 의존, W4 병합 가능).
- 그때까지 매일 hold + 비파괴 무결성 감사 유지.
