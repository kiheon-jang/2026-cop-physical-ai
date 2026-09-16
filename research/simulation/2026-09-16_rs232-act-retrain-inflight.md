# RS232 ACT 재학습 진행 중 (케이블 출구 실기 정합 재수집본) — 2026-09-16

## 요약
9/16 낮 세션이 **케이블 출구를 실기 영상 기준 후드 뒤쪽(커넥터 축)으로 정정** + **측정 판정에 파지(핀치) 확인 추가**(임계 넘는 순간 양 jaw 후드 접촉 조건) 후, 렌더 관측이 바뀌어 100ep 재수집 + ACT 42epoch 재학습을 17:13 착수. 야간 드라이버(`cop_pipeline_advance.sh`) 23:00 시점 STAGE=**학습중**. 본 문서는 그 진행 상태를 문서화한다. 수집/학습/측정 재실행 없음(드라이버 소유).

## 드라이버 STAGE 결과 (23:00, 재실행 아님 — 관측만)
- STAGE=**학습중**
- pid **48360** alive, state `Us`(세션 분리 = 04:04 killer 회피 유효), 시작 17:13
- `train_act.py --epochs 42` → `checkpoints/act_rs232_sim`
- 라이브 **epoch 7/42** step 900, loss **0.0431**(l1 0.0205, kl 0.00226) 정상 수렴
- log mtime 23:01(신선), log_size 8.45MB

## 디스크 검증 (증거)
- **체크포인트**: `checkpoints/act_rs232_sim/` epoch_0009~0041 (mtime Sep 12 04:11 ~ Sep 13 04:57) = **직전 완료 run(케이블 정정 前)** 산물. 새 run 은 epoch 7 이라 아직 epoch_0009(10 epoch마다 저장) 미도달 → 신규 체크포인트 0개. 정상.
- **데이터셋**: `data/episodes_rs232` = **100ep / 16,093frame** (오늘 재수집본, 케이블 출구 정정 반영, yield 84%)
- **마커 3종** (드라이버 MODEL_SIG 규칙 = `DS_BASE:최신 ckpt 내부 최신 mtime`):
  - `cop_trained_on.marker` = `episodes_rs232:1789126035` (케이블 정정 前 완료 모델 = epoch_0041 old)
  - `cop_pending.marker` = `episodes_rs232:1789243031` (재수집본 학습중·대기)
  - `cop_measured.marker` = `episodes_rs232:1789243031` = **낮 세션이 churn 해소용으로 기록한 현 MODEL_SIG**(= epoch_0041 old ckpt mtime, Sep 13 04:57 ≈ 1789243031). measured==현 MODEL_SIG 이라 옛 모델 재측정은 스킵(churn 종료).
- **rollout 산출물**: `rollout_summary_rs232{,_seed7,_seed123,_seed2026}.json` mtime **9/15 23:02~23:06 불변** = 야간 측정 미실행(STAGE=학습중이라 설계대로). 값 = baseline epoch_0041(old) 부분성공 0.875 / 완전분리 0.75.

## 무결성 격리
- `trained_on` = 옛 sig(1789126035) 불변 → baseline(epoch_0041 old) 측정치 무손상.
- 학습 미완 → pending 승격/측정 보류(6/22 SILENT 멈춤 반대·설계대로).
- 새 run 이 옛 체크포인트를 덮어쓰기 전이라 baseline 체크포인트도 물리적 보존.

## 검증 (헬스체크)
- `sim_camera_verification.py` 1회 → **PASS** (top/closeup 듀얼 카메라 30프레임 캡처, `research/simulation/video/`). 학습(pid 48360)과 동시 실행 정상 = 렌더 스택 건강.

## 관찰 / 이슈
- **어제까지의 재측정 churn(9/13~15) 해소 확인**: 낮 세션이 (a) `cop_sim_env.py` 드라이버 호출 timeout 300→600·hermes `script_timeout` 1800→3600, (b) `cop_measured.marker` = 현 MODEL_SIG(`episodes_rs232:1789243031`) 기록. 오늘밤 STAGE=학습중은 churn(동일 재측정 반복)이 아니라 낮에 새로 착수한 재학습의 정상 전진.
- **신규 모델 측정 누락 위험 없음**: MODEL_SIG 이 ckpt mtime 기반이라, 재학습 run 이 epoch_0009+ 를 저장하면 mtime 이 바뀌어 MODEL_SIG 이 갱신됨 → measured(옛 mtime 1789243031)와 불일치 → 드라이버가 **신규 모델(epoch_0041 new)을 자동 재측정**. (dataset-sig 기반이 아니므로 measured==pending 이어도 스킵 안 됨.)
- 신규 체크포인트 0개는 정상(epoch 7 < 첫 저장 epoch 9).

## 다음 단계 연결
- 학습 완주(ETA: epoch 7@23:00, ~2770s/epoch 기준 잔여 35epoch ≈ 9/18 새벽 KST) → 새 ckpt mtime → MODEL_SIG 갱신 → 드라이버가 epoch_0041 new 측정 → 케이블 정정·핀치 판정(및 `*_nopinch_legacy` 병기) 반영된 부분성공/완전분리 재산출.
- 이후 W2 잔여: RS232 DR 합성 + 재학습(로드맵 854, 현 재학습 완주 후 드라이버 새 사이클).
