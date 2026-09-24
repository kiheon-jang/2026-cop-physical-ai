# Phase 4 W2 — RS232 DR 재학습 트리거 발동 + in-flight (2026-09-24)

## 오늘 진행 단계
로드맵 866행 **RS232 DR 합성 + 재학습** — 5일간(9/20~23) 트리거 대기 hold 였던 **재학습 절반이 오늘밤 발동**.
드라이버(`cop_pipeline_advance.sh`)가 nominal 타겟 `episodes_rs232`(STAGE=완료/유지 100ep·0.600)을 닫고
**예약 사이클 `episodes_rs232_dr` 로 전환** → ACT 42epoch 재학습 착수.

## 무엇을 했나
드라이버가 결정론적으로 처리한 STAGE 전환을 확인·문서화. 에이전트는 수집/학습/측정을 재실행하지 않음(하드룰).

드라이버 출력(23:00):
```
STAGE=완료/유지  episodes_rs232 100ep · 최종 성공률=0.6 (목표 0.50)
  ▶ 예약된 다음 사이클로 전환: data/episodes_rs232_dr — 재평가 시작
STAGE=학습시작  (episodes_rs232_dr 100ep 로 ACT 재학습, 42epoch → checkpoints/act_rs232_dr_sim)
[start_act_train] 시작 pid=42079 args=--epochs 42 --no-resume
```

## 어떻게 검증했나 (23:xx 세션 실측)
- **학습 프로세스 alive**: `pgrep train_act.py` → pid **42079** `train_act.py --epochs 42`.
  로그 `train_start`: dataset_root=`data/episodes_rs232_dr`, checkpoint_dir=`checkpoints/act_rs232_dr_sim`,
  epochs=42, resume_from=null, timestamp `2026-09-24T23:00:40`.
- **학습 정상 수렴**: epoch 0 step 10 loss 33.45 → step 20 loss 21.54 (from-scratch 초기 곡선 정상).
- **타겟 전환 확인**: `logs/cop_dataset_target` = `data/episodes_rs232_dr` (`.next` 없음 — 전환 완료).
- **체크포인트 격리**: `checkpoints/act_rs232_dr_sim/` 신규 생성(mtime Sep 24 23:00, 아직 비어 있음 —
  첫 저장 epoch_0009 미도달, 정상). baseline `checkpoints/act_rs232_sim/epoch_0041/model.safetensors`
  mtime **Sep 18 02:42 불변**(335MB).
- **무결성 격리 (baseline 무손상)**:
  - `cop_trained_on.marker` = `episodes_rs232:1789546321` **불변**
  - `cop_measured.marker` = `episodes_rs232:1789666953` **불변**, pending 마커 없음
  - `rollout_summary_rs232.json` mtime **Sep 18 23:02 불변** (부분성공/완전분리 0.600/0.600 = 재측정 없음)
  - datasets: `episodes_rs232` 100ep · `episodes_rs232_dr` 100ep (info.json total_episodes 확인)
  → 학습 미완이라 승격/측정 보류(설계대로, 6/22 SILENT 멈춤 반대) → nominal baseline 무손상.
- env: mujoco 3.8.0 / py 3.14.

## 다음 단계 연결
드라이버가 담당:
1. 42epoch 완주(세션 분리로 04:04 killer 회피, ETA 벽시계 ~9/26 — 직전 RS232 run 이 ~32.5h/42ep) →
2. pending 승격 → `act_rs232_dr_sim/epoch_0041` 4-seed(42/7/123/2026) 자동 측정 →
3. nominal 0.600 vs DR-trained **공정 비교**.

Phase 2 W1 실증(DR 축은 sim 천장 못 올림, 0.825↔0.800)을 RS232 트랙에서 실측 확증하는 것이 이 재학습의 목적.
866 항목은 학습 미완이므로 `[ ]` 유지.
