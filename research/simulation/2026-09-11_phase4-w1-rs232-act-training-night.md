# Phase 4 W1 — RS232 ACT 학습 야간 상태 (STAGE=학습중) — 2026-09-11 23:00

> 드라이버(`cop_pipeline_advance.sh` RS232 분기)가 결정론적으로 전진. 본 문서는 STAGE 결과 기록.
> 오후 세션(`2026-09-11_rs232-real-fidelity-expert.md`)이 실기 정합 재구축 후 **20:27 재수집 데이터로 ACT 재학습 착수**.

## STAGE 결과
- STAGE=**학습중**, pid **55253** alive (`.venv/bin/python3 scripts/train_act.py --epochs 42`)
- 타겟: 데이터=`episodes_rs232`(실기 정합 재수집본, 100ep/16,093f) · ckpt=`checkpoints/act_rs232_sim`
- ckpt_latest=none ckpt_count=0 (epoch<10, 첫 저장 전 — 정상)

## 학습 진행 (metrics jsonl, 재수집 run)
| epoch | loss | l1 | kld | elapsed/ep |
|---|---|---|---|---|
| 0 | 1.902 | 0.113 | 0.179 | 2792s |
| 1 | 0.512 | 0.063 | 0.045 | 2784s |
| 2 | 0.178 | 0.038 | 0.014 | 2782s |
| 3(log tail) | ~0.115 | 0.032 | 0.008 | — |

- 정상 수렴. mps_mem ~8.6GB(16GB 안), rss ~1.0GB 평탄 — OOM/누수 징후 없음.
- epoch당 ~2783s → 42epoch ≈ 32.5h → **ETA ≈ 9/13 05:00 KST**.

## 무결성 격리 (설계대로)
- `cop_trained_on.marker` = `episodes_s1:1785931493` (직전 승격값, **불변**) → baseline 무손상.
- `cop_trained_on.marker.pending` = `episodes_rs232:1789126035` (**대기·미승격**).
- 학습 미완 → 드라이버가 marker 승격·측정 스테이지 보류(6/22 SILENT 멈춤 반대·설계대로).
- 옛 환경 데이터셋은 `data/episodes.bak-rs232-oldenv-20260911` 로 격리 보존.

## 자가치유
- 없음. 학습 프로세스 건강, 마커 정합.

## 다음
- 9/12 야간 = STAGE=학습중 hold 유지 예상.
- 완주(≈9/13) → 드라이버 pending 승격 → `act_rs232_sim/epoch_0041` 측정 → RS232 rollout(부분성공·완전분리). 이후 4-seed 공정추정.
- 미결(오후 세션에서 이월): 야간 측정 300s timeout 초과 위험 미검증 · 근단 x<0.19 기하 상한 ≈37.5% · 실기 실측(보유력·포트 피치) 수신 시 교정.
