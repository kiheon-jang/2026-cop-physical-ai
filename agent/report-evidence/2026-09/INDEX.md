# 2026년 9월 월간 보고서 증거 후보

> 9월 보고서 매핑: Phase 4 W1 — RS232(HHT) 케이블 분리 시뮬 트랙 + 실기 정합 재구축.

## 2026-09-11
- Phase 4 W1 — **RS232 케이블 분리 트랙 착수 + 실기 정합 재구축 + ACT 재학습 in-flight**: `agent/research-log/2026-09-11.md`, `research/simulation/2026-09-11_phase4-w1-rs232-unplug.md`, `research/simulation/2026-09-11_rs232-real-fidelity-expert.md`, `research/simulation/2026-09-11_phase4-w1-rs232-act-training-night.md` → 9월 보고서 [Phase 4 PCB 정비 / RS232 분리] 섹션.
  - **실기 정합(오후 재구축)**: 관절 range 실기 follower 캘리브(pan ±99.9°·lift ±89.5°·elbow ±96.7°·wrist_flex ±93.4°), base 충돌(박스 8+메시 2), forcerange 팔 ±2.94·그리퍼 ±1.47(STS3215 12V), timestep 1/510(정확히 30fps). 실기 텔레옵 parquet(10ep/8762f) 대조로 lift·wrist_flex·elbow 한계 일치 확인. self-check [1]~[9]·[11] PASS.
  - **expert(홀드아웃 67000~67399)**: **349/400 = 0.873** [0.836, 0.902](옛 expert 같은 환경 122/400=0.305). 명령 100% 실기 한계 안, 외력·텔레포트·모델 변경 0, 레포 반영본=검증본 20/20 일치. 근단 x<0.19 상한 ≈37.5%(shoulder 기하 벽, 실측 후 재평가).
  - **재수집 데이터셋**: `data/episodes_rs232` 100ep/16,093frame, yield 84%, 동작 명령·관절값 100% 실기 한계 안(옛 78%). 근단 x<0.19 = 3ep(expert 상한 탓).
  - **ACT 재학습 in-flight**(20:27 착수): pid 55253, `--epochs 42 --no-resume`, `episodes_rs232` → `checkpoints/act_rs232_sim`. 23:30 시점 epoch 3 loss **0.0985** 정상 수렴(epoch0 1.90→), mps ~8.6GB·rss ~1.0GB 평탄, ETA ≈ 9/13 05:00 KST. 04:04 killer 회피(PGID 55253 gateway 분리).
  - **무결성 격리**: `cop_trained_on.marker`=`episodes_s1:1785931493`(불변, baseline S1 무손상) · `.pending`=`episodes_rs232:1789126035`(대기·미승격) · 학습 미완 → 승격/측정 보류(설계대로). 옛 환경 데이터 `data/episodes.bak-rs232-oldenv-20260911` 격리.
  - **미결(측정 대기)**: RS232 4-seed 성공률(부분성공·완전분리)은 9/13 학습 완주 후 측정. 야간 측정 300s timeout 초과 위험(40 rollout × 최대 10.4s ≈ 416s) — 그때 실측. jam 사유 오분류(서보 토크→shoulder 기하 간섭) 정정 필요.

## 2026-09-13
- Phase 4 W2 — **RS232 ACT 학습 완주(42 epoch, `epoch_0041`) + 첫 4-seed 공정추정**: `agent/research-log/2026-09-13.md` → 9월 보고서 [Phase 4 RS232 분리] 섹션.
  - **4-seed 성공률**: 부분성공(≥2.95mm) **0.875 (35/40)** · 완전분리(≥5.9mm) **0.75 (30/40)**. per-seed 부분 0.9/0.7/0.9/1.0(42/7/123/2026), 완전분리 0.7/0.6/0.9/0.8. median 변위 7.99~10.21mm.
  - **완전분리 0.75 > 근단 기하 상한 ≈37.5%(9/11)** — 정책이 근단 약세 배치 상당수 처리. 실패 rollout 이 seed마다 이동(배치 커버리지/모방격차 패턴, floor·DR 트랙과 동일).
  - **측정 timeout 우려 해소**: 실측 **79.6s/seed**(device=cpu, max_frames=240), 개별 seed 프로세스라 300s 무위험. external-deps 결정 불필요.
  - 산출물: `rollout_summary_rs232{,_seed7/123/2026}.json`, history 5종, video `inference_act_rs232_sim_epoch_0041_20260913.mp4`.
  - **관찰(미수정)**: `cop_measured.marker`=`episodes_s1:...` 잔존(rollout 은 rs232 측정 완료) — 다음 사이클 재측정 유발 가능, 관찰만.

## 2026-09-14
- Phase 4 W2 — **RS232 4-seed 재측정 hold (안정 재현) + 시뮬 스택 헬스체크**: `agent/research-log/2026-09-14.md` → 9월 보고서 [Phase 4 RS232 분리] 섹션.
  - **4-seed 재측정**(동일 `epoch_0041`, 결정론적): 부분 **0.875 (35/40)** · 완전분리 **0.75 (30/40)** — 9/13 과 완전 일치 = 결과 안정 재현. wall time 78.7~79.3s/seed(2일 연속 안정).
  - **렌더 헬스체크**: `sim_camera_verification`(듀얼 30f)·`sim_headless_6dof_video`(2501f) 둘 다 PASS → 시뮬 스택 무회귀.
  - **재측정 churn 확정(2일 연속)**: `cop_measured.marker`=`episodes_s1` stale 로 드라이버가 매 야간 동일 4-seed 재측정. 무해(결정론적·~319s·baseline 무손상)하나 근본=드라이버 measured 승격 누락. 자가치유 미실행(하드룰상 마커 직접수정 회피).

## 2026-09-15
- Phase 4 W2 — **RS232 4-seed 재측정 hold (3일 안정 재현) + 렌더 헬스체크**: `agent/research-log/2026-09-15.md` → 9월 보고서 [Phase 4 RS232 분리] 섹션.
  - **4-seed 재측정**(동일 `epoch_0041`, 결정론적): 부분 **0.875 (35/40)** · 완전분리 **0.75 (30/40)** — 9/13·9/14 와 완전 일치 = 3일 안정 재현. wall time 79.5~79.7s/seed(3일 연속 안정).
  - **렌더 헬스체크**: `sim_camera_verification`(듀얼 30f)·`sim_headless_6dof_video`(2501f) 둘 다 PASS → 시뮬 스택 무회귀.
  - **재측정 churn 3일차**: 근본=드라이버 measured 승격 누락(마커 stale). external-dependencies.md 에 표면화. 자가치유 미실행(드라이버 소유).

## 2026-09-16
- Phase 4 W2 — **RS232 실기 정합(케이블 출구·측정 핀치 판정) + churn 해소 + ACT 재학습 in-flight + 렌더 헬스체크**: `agent/research-log/2026-09-16.md`, `research/simulation/2026-09-16_rs232-act-retrain-inflight.md`, `research/simulation/2026-09-16_session-handoff.md` → 9월 보고서 [Phase 4 RS232 분리] 섹션.
  - **재측정 churn(9/13~15) 근본원인 확정·해소**: 드라이버 `cop_sim_env.py` timeout 300s < RS232 측정 ~318s → 3일 연속 exit 2 → 23:00 잡 Claude 단계 미실행(진척률 0.722 고착). 조치: measured 마커 기록 + timeout 600/3600 상향.
  - **케이블 출구 실기 정합**: 옆(-y) → 후드 뒤쪽(커넥터 축) 정정. 동작 무영향(시각 전용, 동일 시드 5/5 동일) 확인 후 렌더 관측 변경분 재수집.
  - **측정 판정 보강**: 부분성공에 파지(핀치) 확인 추가(양 jaw 후드 접촉), 목표치·임계 불변, `*_nopinch_legacy` 병기.
  - **ACT 재학습 in-flight**: pid 48360, `--epochs 42`, `episodes_rs232`(100ep/16,093f 재수집본) → `checkpoints/act_rs232_sim`. 23:00 epoch 7/42 loss 0.0416 정상 수렴, 완료 예상 9/18 새벽. 야간 측정 hold(설계대로).
  - **렌더 헬스체크(23:30)**: `sim_camera_verification`(듀얼 30f)·`sim_headless_6dof_video`(2501f, ≈6.5ms/frame) PASS(학습 동시). `sim_pick_place` = Phase 0 레거시 결정론적 0%(무회귀).
  - **baseline(옛 케이블·옛 판정)**: 부분성공 0.875 / 완전분리 0.75, 사이트 진척률 0.750(D-45). 새 기준 수치는 9/18 재측정 후 병기.

## 2026-09-17
- Phase 4 W2 — **RS232 ACT 재학습 in-flight Day 2 + 근거 분석 4종(옛 가중치 고정 측정) + 렌더 헬스체크**: `agent/research-log/2026-09-17.md`, `research/simulation/2026-09-17_rs232-act-retrain-inflight-day2.md`, `research/simulation/2026-09-17_rs232-retention-operating-envelope.md`, `research/simulation/2026-09-17_rs232-three-way-decomposition.md`, `research/simulation/2026-09-17_s1-dr-gate.md`, `research/simulation/2026-09-17_task-transfer-record.md` → 9월 보고서 [Phase 4 RS232 분리 / 기능 완성] 섹션.
  - **보유력 운영 범위**(옛 가중치 `_published_baseline_20260913/epoch_0041`, seed42×10, 씬 불변): 보유력 1.75~12 N 평탄(옛기준 부분 0.9→0.8), **20 N 에서 붕괴**(부분 0.6·완전 0.3). 7.2 N 공표값이 override no-op 로 운영 baseline 0.9/0.7 재현 = 스윕 도구 타당성 확인. → 공표 수치는 추정 보유력에 민감하지 않음(≤12 N 안정). 당김 저울 1회 실측이 곡선을 예측으로 전환.
  - **3자 분해(기하/판정/재학습)**: 9/16 3변경을 옛 가중치 고정으로 분리 — ① 케이블 기하(A→B) 옛판정 **+0.00**(중립 재확인)이나 파지 스텝 중앙값 936→592 저하(옛판정이 못 봄) · ② 판정(핀치) 변경 옛씬 −0.30/새씬 −0.60(파지 품질 의존) · ③ 재학습 효과는 9/18 측정 후 확정(기준점 부분 0.3/완전 0.4). → 내일 낮은 수치의 원인은 ②+③이지 기하 아님.
  - **S1 DR 게이트**(RS232 DR 32.5h 재학습 정당성): DR 학습 정책 교란 하 0.45→**0.80**(유의) 강건성 실증, 그러나 공칭 0.925→**0.675**(−0.25 유의) 거래. → 권고 **(나) DR 재학습하되 공칭·교란 병기**(기준 변경 없이 이득 가시화). 운영 S1 산출물 mtime 불변 확인.
  - **과제 이식 속도 기록**(내재화 증거): pick&place ~40일 → S1 **1일** → RS232 **2일**. 재사용=학습기/데이터규약/측정규약/드라이버/야간자동화, 신규=씬·전문가·판정 3종뿐. 저장소 459커밋(440 1인), Mac mini M5 16GB 1대. **10월 발표 헤드라인 후보**(성공률은 그 아래 증거).
  - **렌더 헬스체크(23:30, 학습 비경합)**: `sim_camera_verification` 3회 3/3(듀얼 30f)·`sim_headless_6dof_video` 2501f 둘 다 PASS → 시뮬 스택 무회귀.
  - **학습 진척**: pid 48360 alive, epoch 38/42 loss 0.0084, ETA ~03:00 9/18. 승격/측정 보류(설계대로) → baseline 무손상.
  - ⚠ **정직성 단서(전 문서 공통)**: 모두 시뮬 측정, 실물 검증 없음 · n=10~40 CI 넓음(소수 둘째 자리 주장 금지) · 커넥터 보유력·잭스크류 체결 실측 없음.

## 2026-09-18
- Phase 4 W2 — **RS232 ACT 재학습 완주 + 4-seed 공정추정 측정(정합·핀치 baseline 확정) + 렌더 헬스체크**: `agent/research-log/2026-09-18.md`, `research/simulation/2026-09-18_rs232-corrected-baseline-4seed-measurement.md` → 9월 보고서 [Phase 4 RS232 분리] 섹션.
  - **RS232 정합·핀치 baseline 확정**: 신 핀치 판정 4-seed 평균 **부분성공 0.600 · 완전분리 0.600**(seed 42/7/123/2026), legacy(옛 비핀치) 0.925/0.825. **완료 기준(부분 40%) 0.600 > 0.40 PASS**. 재학습 02:42 완주(`act_rs232_sim/epoch_0041`, 42epoch from-scratch). churn(9/13~15) 재발 없음(마커 정합).
  - **핀치 판정 하락은 성능 하락 아님**: 비핀치 false-positive(누르고 끌기) 제거. legacy 0.925/0.825 > 9/13 옛 baseline 0.875/0.75 → 모델 자체 소폭 개선.
  - **렌더 헬스체크(23:30)**: `sim_headless_6dof_video`(2501f)·`sim_camera_verification`(듀얼 30f)·`sim_data_collector` 스모크 2/2 yield 100% lift 43.3mm PASS. `sim_pick_place` = Phase 0 레거시 결정론적 fail(approach 0.32m, 무회귀). 시뮬 스택 무회귀, mujoco 3.8.0/.venv.

## 2026-09-19
- Phase 4 W2 — **RS232 수집기 DR 배선 + DR 데이터셋 합성 + 렌더 헬스체크**: `agent/research-log/2026-09-19.md`, `research/simulation/2026-09-19_phase4-w2-rs232-dr-wiring-synthesis.md` → 9월 보고서 [Phase 4 RS232 분리] 섹션.
  - **RS232 수집기 DR 배선**(`sim_rs232_unplug_collector.py`): S1 수집기와 동일 계약(`COP_COLLECT_DR=1` env-gate·카메라노이즈·reset restore→randomize→mj_setConst), 환경치수 불변(조명/마찰/카메라만), 기본 off → nominal 파이프라인 불변. DR 스모크 2/2·비파괴 원복 단위검증 PASS.
  - **DR 데이터셋 합성**(`data/episodes_rs232_dr`, 100ep): 23:00 잡 6/100 중단(부모-사망 킬) → 23:30 잡 detached 재기동(PID 29014)으로 완주 처리. 완주 검증=`meta/info.json` total_episodes=100(내일). 격리: 운영 `episodes_rs232`·`rollout_summary_rs232.json`(0.600) 불변.
  - **렌더 헬스체크(23:30)**: `sim_headless_6dof_video`(2501f, 9.4s)·`sim_camera_verification`(듀얼 30f)·`sim_data_collector` 스모크 2/2 yield 100% lift 43.4mm PASS. `sim_pick_place` = 레거시 결정론적 fail(approach 0.323m, 무회귀). mujoco 3.8.0/.venv.

## 2026-09-20
- Phase 4 W2 — **RS232 DR 합성 완주 확인 + 재학습 트리거 준비 + 렌더 헬스체크**: `agent/research-log/2026-09-20.md`, `research/simulation/2026-09-20_phase4-w2-rs232-dr-synthesis-complete.md` → 9월 보고서 [Phase 4 RS232 분리] 섹션.
  - **DR 합성 완주 확인**: `data/episodes_rs232_dr` total_episodes=100·total_frames=15,337·fps=30(info.json 직접 파싱), 9/19 detached 재기동(PID 29014) 정상 종료. 격리: nominal `episodes_rs232`·`rollout_summary_rs232.json`(0.600, Sep 18) 불변, 회귀 0.
  - **렌더 헬스체크(23:30)**: `sim_headless_6dof_video`(2501f)·`sim_camera_verification`(듀얼 30f)·`sim_data_collector` 스모크 2/2 yield 100% lift 42.6mm PASS. `sim_pick_place` = 레거시 open-loop 결정론적 fail(approach 0.323m, 무회귀). mujoco 3.8.0/.venv.
  - **재학습 절반 = 드라이버 담당**: `cop_dataset_target`→`episodes_rs232_dr` 전환/마커 삭제 시 42epoch 재학습→DR-trained 4-seed→nominal 0.600 비교. 에이전트는 준비 완료만 표면화(하드룰상 직접 학습 안 함).
