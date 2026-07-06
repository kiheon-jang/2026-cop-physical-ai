# Phase 2 W1 — 파이프라인 적대적 감사(19건 확정) + DR 재학습 트리거 (2026-07-06 주간)

## 요약
어제까지 3일째 "트리거 결손"으로 대기하던 **DR 재학습(W1 잔여 절반)을 오늘 13:31 실제 트리거**했다
(pid 74621, `episodes_cl_dr` 50ep → `checkpoints/act_cl_dr`, 100epoch, ETA ~22:30).
트리거 전에 멀티에이전트 적대적 검증으로 파이프라인 코드 결함 32건 후보를 검증해 **19건 확정 / 13건 반증 기각**,
그중 "그냥 트리거하면 W1 비교 실험이 깨지는" critical 6건을 먼저 수정했다.

## 왜 수정 없이는 트리거가 불가능했나 (확정 critical)
| # | 결함 | 파일 | 결과 |
|---|---|---|---|
| 1 | `sig()`가 디렉터리 mtime → `save_pretrained` in-place 덮어쓰기 미감지 | cop_pipeline_advance.sh | 재학습 후 측정(stage 5) 조용히 스킵, 옛 0.70이 새 모델 성적으로 보고 (epoch_0099 디렉터리 6/22 vs 내부 파일 6/25로 디스크에 이미 실증) |
| 2 | `DATA_DIR` 하드코딩 + `COP_DATASET_ROOT` 무조건 export | cop_pipeline_advance.sh | 드라이버 경유 DR 학습 원천 불가. 마커 삭제로 우회 시 **엉뚱한 episodes_cl 로 재학습** |
| 3 | 체크포인트 경로에 데이터셋 구분 없음 | train_act.py | DR 재학습이 CL baseline 모델(0.70)을 그 자리에서 파괴 |
| 4 | nominal 측정이 `rollout_summary.json` 무조건 덮어씀 | render_act_rollout.py | baseline 0.70 기록 소실 |
| 5 | `find_latest_checkpoint` 디렉터리 mtime 정렬 | render_act_rollout.py | in-place 재학습과 결합 시 엉뚱한 모델 측정 |
| 6 | `TRAINED_MARK`를 학습 '시작' 시점 기록 | cop_pipeline_advance.sh | 학습 중도 사망 시 영구 침묵, 반쯤 덮인 체크포인트가 '완료' 취급 |

## 적용한 수정 (전부 커밋됨)
- **드라이버** `scripts/cop_pipeline_advance.sh`:
  - 데이터셋 타겟 = `logs/cop_dataset_target` 파일 (cron 은 env 를 안 넘기므로 영속 상태는 파일).
    현재 값: `data/episodes_cl_dr`.
  - 체크포인트 데이터셋별 격리: `episodes_cl`→`checkpoints/act`(레거시), `episodes_cl_dr`→`checkpoints/act_cl_dr`.
  - `sig()`: 디렉터리는 내부 파일 최신 mtime. 마커 형식 `"<ds>:<sig>"` (구형식은 자동 불일치 → 안전).
  - 학습 마커 2단계: 시작 시 `.pending` → **stage 2.5 에서 metrics jsonl 로 완료 검증 후 승격**
    (이상종료면 pending 삭제 + 재시도 예약 + 로그 표면화). 승격 후 같은 실행에서 측정까지 fall-through.
  - stage 3 가드: `info.json` 존재하는데 카운트 0 이면 수집 시작 안 함 (운영 데이터 보호).
  - `pid_alive`: stale pid 파일 자동 정리 + 커맨드 패턴 검사 (PID 재사용 오탐 방지).
- **학습기** `scripts/train_act.py`: `COP_CKPT_DIR` env, 시작 배너(train_start: dataset/ckpt/epochs),
  metrics jsonl 에 `dataset`/`ckpt_dir` 식별자, dataset_root 존재 검증(fail-fast), resume 가중치-only 경고.
- **측정기** `scripts/render_act_rollout.py`: `COP_CKPT_DIR` + model.safetensors mtime 정렬,
  summary 에 `measured_at`/`ckpt_dir`/`seed`, `--summary-suffix`(수동 비교용),
  **불변 히스토리 사본**(`inference_progress/history/`) + **3D 리플레이 궤적 덤프**
  (`rollout_traj_latest.json`, qpos6+cube_xyz per 정책스텝 — 웹 대시보드 3D 뷰어 데이터원),
  영상 파일명에 ckpt/dr/seed 태그 (동일날 측정 상호 덮어쓰기 방지).
- **수집기** `samples/training/sim_data_collector.py`: `rmtree` → 타임스탬프 백업 rename, `--seed`(재현성).
- **베이스라인 아카이브**: `rollout_summary_baseline_cl.json` + `history/20260625-2300_act_epoch_0099_baseline_cl.json`.

## 반증 기각 13건 (수정 안 함 — 사유 기록)
측정 실패 시 truncation, TOCTOU 이중 실행, MPS fallback env 시점, dataclass env 평가 시점,
정규화 미적용(lerobot 0.5.1 정책 내부 처리), --dry-run 죽은 플래그, dr_rng 시드 상관,
수집 미달 exit 0, rollout 예외의 성공률 오염, SETTLE_STEPS 80 vs 100 주석, docstring 50mm 표기 등 —
전부 "코드 사실은 맞으나 문서화된 운영 시나리오에서 오동작 없음"으로 고신뢰 기각.
(단, headlight 미랜덤화로 light DR 축이 실질 약화되는 건은 **실재** — 아래 후속.)

## 후속 (W1 이후)
1. **light DR 강화**: `sim_domain_randomization.py`가 `model.vis.headlight`(씬 지배 광원)를 안 건드림 —
   이미 합성된 `episodes_cl_dr`와의 일관성 때문에 이번 사이클엔 미적용. 다음 DR 세대에서 headlight 포함 재설계.
2. **큐브 크기 축 DR 없음**: 현 DR 은 조명/마찰/카메라뿐. 실물 3~5cm 박스 대응은
   ①크기 랜덤화(25~50mm) ②expert 상수 재튜닝(APPROACH_GRIP≥0.95, CLOSE_Q≈0.7) ③재수집 필요.
   치수 검증 결과: 그리퍼 개구(손끝 94.5mm/패드 70mm)는 50mm 커버 — **하드웨어 문제 아님** (별도 문서 참조).
3. **통계력**: n=10 단일시드로는 0.70 대비 ±0.1 차이 판별 불가 — DR 모델 측정 후
   `--summary-suffix _seed{7,123,2026}` 다중시드 공정추정(baseline 프로토콜과 동일)으로 비교할 것.

## 오늘 트리거 상태
- 13:31 학습 시작 확인: `train_start` 배너 = dataset `episodes_cl_dr` / ckpt `act_cl_dr` / 100epoch.
- loss 정상 하강(step40 loss 12.9). ETA ~22:30 → 23:00 크론이 stage 2.5 승격 + stage 5 측정 예상.
- 측정 산출: 새 `rollout_summary.json`(operational latest) + history 사본 + `rollout_traj_latest.json`.
  baseline 은 `rollout_summary_baseline_cl.json` 으로 보존.
