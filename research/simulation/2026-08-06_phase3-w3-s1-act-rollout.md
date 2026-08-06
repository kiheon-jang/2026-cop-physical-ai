# Phase 3 W3 — S1 리셋버튼 ACT 학습 + 롤아웃 측정 (2026-08-06)

> W3 dated 범위(8/19~8/25)를 **조기 완주**. 8/5 야간 착수한 S1 ACT 학습이 8/6 오전 완료 →
> 8/6 오후 4-seed LED-latch 롤아웃 측정 완료. 드라이버 STAGE=완료/유지(episodes_s1·sr 0.925).
> 이 문서는 드라이버가 낸 결과를 문서화한다(파이프라인 재실행 없음).

## 무엇을 했나

### 1) S1 ACT 학습 완주 (04:04 killer 관통)
- `scripts/train_act.py --epochs 30`, dataset `episodes_s1`(100ep/7,231f, top+closeup 2카메라),
  ckpt `checkpoints/act_s1_sim`. W3 인에이블러(`COP_CAMERA_KEYS`/`COP_DATASET_REPO_ID`, 8/5)가
  실발효 → 2카메라 데이터로 학습.
- PID 65874, 8/5 22:59 시작 → **8/6 09:37 완료** (epoch_0029 저장). wall_clock **38,065s(~10.6h)**,
  최종 loss 0.0133.
- **04:04 killer 관통 확증**: `start_act_train.sh` 의 `start_new_session`(새 프로세스 그룹) 분리로
  `ai.hermes.autoupdate`(04:00 launchd) 의 gateway kickstart 그룹 SIGKILL 을 회피 → 학습이 04:04 를
  넘겨 생존(epoch_0019 06:11 · epoch_0029 09:37). external-dependencies.md 8/6 종결 항목과 정합.

### 2) 4-seed 롤아웃 측정 (LED latch 자동 채점)
- `scripts/render_act_rollout_s1.py` (신규, pick-place `render_act_rollout.py` 의 S1 판본).
  씬=`pcb_reset_scene.xml`(버튼 치수·스프링·존 = 실기 기준, 환경 불변), 성공 판정 = **LED latch**
  (P1 녹색 LED 계약과 동일 — 슬라이드 조인트 변위 임계 1.5mm 넘으면 점등 유지).
- ckpt `act_s1_sim/epoch_0029`, seed당 N=10, 측정 8/6 14:47~14:50 (cpu, seed당 ~49s).

| seed | success | 성공률 | median press(mm) |
|---|---|---|---|
| 42 (nominal) | 9/10 | **0.90** | 3.67 |
| 7 | 9/10 | 0.90 | 2.13 |
| 123 | 10/10 | **1.00** | 2.86 |
| 2026 | 9/10 | 0.90 | 3.37 |
| **4-seed 평균** | **37/40** | **0.925** | — |

- **완료 기준 0.70(LED 자동 판정) 초과 달성** — nominal 0.90, 공정추정 평균 0.925.
- press 변위 median 2.1~3.7mm 전부 임계 1.5mm 위 = 여유 있는 latch(경계 아님).
- 실패 3/40 = expert 95% 규명 때의 존 구석 기하 도달불가 배치와 동류(같은 SO-101 이라 실기도 동일).

## 어떻게 검증했나
- `rollout_summary_s1.json` + `_seed{7,123,2026}.json` (status ok, metric led_latch, ckpt epoch_0029).
- history 덤프 5종 `inference_progress/history/20260806-1447*_act_s1_sim_epoch_0029*.json`
  (+ seed42 `_traj.json` = 3D 리플레이 궤적) → 대시보드/리플레이가 glob 자동 소비.
- 학습 로그 `logs/s1_train_30ep.log` tail = `"학습 30 epoch 완료"`, ckpt 디렉터리 mtime
  (epoch_0019 06:11 · epoch_0029 09:37) = 04:04 관통 물증.
- 롤아웃 영상 `inference_progress/inference_act_s1_sim_epoch_0029_20260806.mp4`(seed42).

## 다음 단계로의 연결
- W3 두 항목([ ] ACT 학습 · [ ] rollout 측정) **완료 → [v]**. Phase 3 완료 기준(성공률 70%) 충족,
  남은 완료 기준 = "합성 데이터셋 omen 로드 확인"(W2/W4 외부 협업).
- **W4(8/26~) sim2real 핸드오프**: sim-trained 정책(`act_s1_sim/epoch_0029`) + `episodes_s1` 를
  omen 전달(실기 fine-tune 대조군) · P1 LED ROI 캘리브 지원 · Sim2Real 격차 보고.
- 측정 방법 간극(학습=h264 디코드 프레임 vs rollout=무손실 raw 렌더)은 render 스크립트에 명시,
  resnet18 영향 작음 — W4 실기 격차 보고 때 재확인.
