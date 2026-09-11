# Phase 4 W1 — RS232(HHT) 케이블 분리 시뮬 트랙 착수 (2026-09-11)

> 엘리베이터 PCB 제어반 정비 3단계 "RS232 케이블 분리(꽂힌 HHT 케이블 플러그 빼기)" 시뮬 트랙.
> 2단계 S1 리셋버튼 구현(`pcb_reset_scene.xml` / `sim_pcb_reset.py` / `sim_pcb_reset_collector.py` /
> `render_act_rollout_s1.py`)과 같은 구조·같은 규약으로 만들었다. W1 체크 4항목의 게이트는 모두 통과했다.
> 다만 expert 새 시드 성공률은 합격선에 딱 걸렸고(0.75), 실패 원인 분류 검증 1건은 **불합격**이다(아래).
> ACT 학습은 착수만 했고 완료·측정 전이다.
>
> **2026-09-11 오후 갱신**: 실기 정합(관절 한계·base 충돌 등)으로 트윈·expert·데이터셋을 다시 만들었다. 이 문서의 expert·데이터셋·학습 수치는 옛 환경 기준이다 → `2026-09-11_rs232-real-fidelity-expert.md`.

## 1. 무엇을 만들었나

| 산출물 | 경로 | 비고 |
|---|---|---|
| 씬 | `sim/assets/rs232_unplug_scene.xml` | SO-101 include, top/closeup 카메라·PCB 15×15cm 는 S1 과 동일. DE-9 포트 2개 + HHT 플러그(슬라이드 조인트) |
| 트윈 모듈 | `samples/training/sim_rs232_unplug.py` | S1 존 상수 import, 관통 배치 재추첨 reset, FULL/PARTIAL latch, render, `_self_check` 7항목 |
| expert + 수집기 | `samples/training/sim_rs232_unplug_collector.py` | S1 `PressExpert`(IK·record 훅) 상속, 무관통 파지 계획 → 핀치 → 커넥터 축 당김, LeRobot v3 합성 + `meta/pcb_traj.json` 사이드카 |
| 측정기 | `scripts/render_act_rollout_rs232.py` | S1 판본 규약 그대로, 4-seed × 10, `rollout_summary_rs232*.json`. success_rate = 부분성공, full_rate 병기 |
| 드라이버 분기 | `scripts/cop_pipeline_advance.sh` (RS232 분기 +19줄) | TARGET_EP 100 / TARGET_RATE 0.50, ckpt `checkpoints/act_rs232_sim`, 2카메라 env, pick-place 수집기 차단 |
| 대시보드 라벨 | `dashboard/build.py` (+4줄) | `rollout_summary_rs232*.json` 표시명 |
| 데이터셋 | `data/episodes_rs232` | 100ep / 16,024frame / 시도 132 / yield 0.758, repo_id `local/rs232_unplug_sim`, task `"unplug the rs232 cable"` |

모두 미커밋 상태다(메인 세션 검토 후 커밋).

## 2. 어떻게 검증했나 (검증자가 직접 실행한 결과, 수치 그대로)

### 2.1 트윈 + 판정 — PASS
`sim_rs232_unplug.py` self-check **7/7 PASS** (3회 실행 로그 동일):
- [1] 그리퍼 충돌 geom 3개 ↔ 후드 접촉 필터 활성(exclude 아님), 보유력 frictionloss 7.2N
- [2] seed 42 배치 재현
- [3] 무작위 리셋 200회: 관통 없음, 관통 배치 거부 45회(거부율 18.4%), 후드 top 프러스텀 200/200, 두 카메라 중 하나 이상 가시 200/200(closeup 최소 725px). **top 팔 가림: 완전 가림 14/200, 가시 <50% 64/200, 평균 가시 67%**
- [4] 무접촉 중력만 3초 변위 0.0000mm
- [5] 외력 당김: 0.8×(5.76N) 2초 0.0768mm / 이탈 시작 7.30N(DE-9 규격 대역 1.76~30.1N) / 1.5×(10.8N) PARTIAL 6ms·FULL 8ms, 되밀어도 latch 유지 / 0.95×(6.84N) 3초 0.137mm latch 없음
- [6] 물리 파지-당김 25배치: 충돌 없는 파지 직전 자세 21/25, 핀치 FULL 21/21, slip/TCP이동 비 중앙 -0.05·최대 -0.03, jaw 열림 대조군 FULL 0/21·최대 변위 0.000mm
- [7] top/closeup 640×480 렌더

### 2.2 expert — PASS (단, 3번 항목 불합격)
제작자 측정: 20-seed 0.95. 검증자 측정은 아래.

| # | 항목 | 결과 | 값 |
|---|---|---|---|
| 1 | 새 시드 1000~1019 `--expert-eval` (합격선 ≥0.75) | PASS | **15/20 = 0.75**, 합격선에 딱 걸림(첫 검증 라운드는 14/20 = 0.70 으로 불합격 → expert 수정 후 재검증한 결과). 1차 시도 성공 14/20 = 0.70. 실패 5: unreachable 3(1003·1008·1011), jam 2(1006·1015). 10+10 분할 실행과 20 단일 재실행 per_seed JSON 동일(결정론) |
| 1b | 추가 미사용 시드(과적합 점검) | PASS | 5000~5019: 19/20 = 0.95(1차 17/20). 7000~7099: 85/100 = 0.85(1차 82/100), 실패 unreachable 8·margin_blocked 4·approach_blocked 2·jam 1 |
| 1b | 140시드 PCB x 구간별 | — | [0.15,0.19) **2/19 = 0.11** · [0.19,0.22) 23/27 · [0.22,0.26) 43/43 · [0.26,0.30) 51/51 → **존 근단에서 사실상 실패** |
| 2a | 당기는 동안 그리퍼-플러그 실제 접촉 | PASS | 55,050스텝 감사. 성공 15건 모두 플러그가 빠지는 스텝에 gripper/moving_jaw 접촉. 그리퍼 축방향 힘 중앙 7.2N(=frictionloss). 다른 팔 링크가 빼는 방향으로 민 힘 15건 모두 최대 0.0N. 1002 의 비접촉 이동 9스텝은 접촉 없음·변위≤0(조인트 한계 되튐) |
| 2b | 플러그 qpos 직접 대입 | PASS | 스텝 간 qpos 점프 최대 0.0, 적분 오차 최대 2.2e-16. collector 가 쓰는 qpos 는 별도 MjData `d_ik` 뿐 |
| 2c | 실행 중 마찰·질량·보유력·솔버 변경 | PASS | MjModel 전 ndarray + opt 해시 비교 변경 0건(시작=끝, 500스텝마다). xfrc/qfrc_applied 비0 스텝 0, ctrlrange 초과 0. geom 마찰 최대 1.0 등 전부 XML 정적값 |
| 2d | 판정 상수 트윈에서 import | PASS | collector `from sim_rs232_unplug import ... UNPLUG_FULL_M`, PULL_DISP = 1.5×UNPLUG_FULL_M, FULL latch 는 `twin.step` 에서 슬라이드 qpos 로 판정 |
| 3 | 실패 2건 렌더 확인 + 분류 검증 | **FAIL** | 아래 2.3 |
| 4 | S1 파일 무변경 | PASS | `git diff --stat` 에 S1 없음, S1 추적 4파일 HEAD clean, `episodes_s1`·`act_s1_sim`·`rollout_summary_s1*` 9/1 이후 수정 없음 |

### 2.3 실패 분류 검증 불합격 내용 (3번)
- **1003 (unreachable)** — 분류 맞음. 계획을 무시하고 강제 실행해도 approach_blocked(moving_jaw↔rs232_port_2 -1.16mm, ↔pcb -0.73mm, 접근 오차 28.9mm). 렌더상 후드가 shoulder 에 붙어 있음.
- **1015 (jam)** — 범주는 맞지만 **제작자가 붙인 원인(서보 토크 한계)은 틀림**. 스테이지별 접촉력 측정: FULL 직후 변위 5.91mm 에서 **shoulder 링크가 후드를 반대로 밀고**(-5.3N → -11.0N 증가), 액추에이터 포화는 그 결과. 렌더에서도 후드 바로 뒤에 shoulder 베이스가 보임.
- **1006** — 같은 메커니즘(당김 중 shoulder -11~-15N). 접근 단계에서 이미 shoulder 가 후드를 -10.8N 으로 밀어 넣음(변위 -0.25mm).
- 결론: jam 은 토크 부족이 아니라 **존 근단 기하 간섭**이다. unreachable 과 뿌리가 같다.

### 2.4 데이터셋 + 드라이버/학습 착수 — PASS
- `data/episodes_rs232`: `meta/info.json` v3.0, total_episodes 100, total_frames 16,024, fps 30, top+closeup 640×480 video. 수집 로그 "수집 완료: 100/100 (시도 132, yield 76%)". 저장 정책 = **1차 시도 성공 에피소드만**.
- 저장된 100ep 의 PCB x 분포(`meta/pcb_traj.json`, 이 문서 작성 시 계산): [0.15,0.19) 3 · [0.19,0.22) 21 · [0.22,0.26) 33 · [0.26,0.30) 43, 최소 x 0.164.
- 드라이버 착수(9/11 13:06, `COP_EPOCHS` unset): `타겟: 데이터=episodes_rs232 ckpt=checkpoints/act_rs232_sim` → STAGE=학습시작, pid 31176, `--epochs 42 --no-resume`, pending marker `episodes_rs232:1789099088`. 13:07 재실행 STAGE=학습중(pending 유지, 재학습 미트리거).
- epoch 0 metrics: steps 2003, loss 1.877, elapsed 3,166.4s, mps_mem 9.47GB, dataset=episodes_rs232, ckpt_dir=act_rs232_sim.
- 학습 프로세스 pid 31176 은 자기 프로세스 그룹 리더(PPID 1, PGID 31176) — gateway(pgid 23312) 와 분리(04:04 killer 회피 구조, S1 과 동일).
- ETA: 42 × 3,166s ≈ 36.9h → **2026-09-13 02:00 KST 전후**(epoch 0 외삽만, 에폭 중 스텝 시간이 1.36→1.7 s/step 로 늘어남).
- **학습 완료·측정은 아직 없다.** 성공률 수치는 없음.

## 3. 실기 프레임 근거
실기 영상 프레임 2장(top·closeup)을 직접 확인했다.
- closeup: 빨간 PCB 앞 가장자리(카메라·그리퍼 쪽)에 금속 D-sub 포트 2개(실크 S3, S2)가 판면과 나란히 앞을 향해 달려 있고, 그 오른쪽에 베이지 후드가 같은 방향으로 꽂혀 있으며 케이블이 후드에서 빠져나간다. 노란 그리퍼 jaw 가 가장자리 앞에 있다.
- top: PCB 가장자리에 베이지 후드 + 케이블, 오른편에 HHT 단말, 화면 아래쪽에 팔.
- 따라서 분리 = 후드를 잡고 **팔 쪽으로 수평으로 당김**(들어올리기 아님) → 씬에서 슬라이드 축 = PCB 로컬 -x.
- **확인 필요**: closeup 에서 후드가 꽂힌 포트 자체는 후드에 가려 보이지 않는다. "2포트 중 오른쪽"(현 씬 모델)인지 S2 오른쪽의 별도 포트인지는 이 프레임만으로 확정할 수 없다. 실측 시 포트 간격(현재 36mm 목측값)과 함께 확인해야 한다.

## 4. 설계 결정 (근거)
- **환경 불변**: 카메라 2대·PCB 치수·존(x 0.15~0.30, y ±0.075, yaw ±10°)은 `sim_pcb_reset` 상수 import. 존 근단에서 플러그/포트(팔 쪽 ~37mm 돌출)가 홈 자세 shoulder 메쉬와 겹치는 배치는 물리적으로 불가능한 초기 상태라 **존은 그대로 두고 관통 배치만 재추첨**(거부율 18.4%). S1 씬도 같은 존에서 보드↔팔 관통 배치가 5.0% 나옴(rng0 200회 중 10회, 최대 8.8mm) — S1 은 수정 금지라 기록만.
- **커넥터 치수 (DE-9, E 쉘)**: Adam Tech DXXX-SR 도면 DE09 행 — 플랜지 30.81×12.55mm, D 쉘 돌출 5.90mm(.232"), 쉘 외형 16.33×7.90mm(사다리꼴을 박스로 근사). 후드 31×15.5×30mm(표준 백쉘 근사). 포트 간격 36mm 는 실기 근접 프레임 목측. 치수를 키우지 않았다.
- **보유력 7.2N**: Cinch M24308(MIL-C-24308) 접점당 삽입·분리력 0.7oz/12oz = 0.195/3.34N. 9핀 대역 1.75~30N. 대역 로그 중앙 √(0.195×3.34)=0.81N × 9 ≈ 7.2N → 슬라이드 `frictionloss="7.2"`(쿨롱, 단일 출처 = XML). 잭스크류 미체결 가정. **실측(당김 저울) 수신 시 교정할 노브.**
- **판정 임계**: FULL = 5.90mm = D 쉘 최대 결합 깊이(핀은 쉘 안이라 핀 결합 ≤ 쉘 깊이 → 더 엄격한 쪽 채택). PARTIAL = FULL/2 = 2.95mm, 규격값이 아닌 정의값이며 부분성공 지표 전용. expert 시연 채택은 더 엄격(핀치 확인 + FULL + 변위 ≥ 1.5×FULL).
- **플러그 크리프 억제**: MuJoCo frictionloss 는 소프트 제약이라 기본값에선 보유력 이하에서도 미끄러짐(0.8× 2초 43.8mm 실측) → `solimpfriction 0.9999…`, `solreffriction 0.004`(2×dt). 보유력 크기는 불변. `solreflimit 0.004` 는 40mm 케이블 여유 한계 관통 방지.
- **파지 접촉(slip) 수정 = (c)+(a)**: 후드 `priority=1 solref=0.004 solimp=0.99…` + `<option cone="elliptic" impratio="10"/>`(이 씬 한정). 25배치 동일 레시피 비교: 기본 0/25(slip 비 1.00) · (c) 단독 18/25(slip 중앙 0.32) · (a) 단독 17/25 · (b) noslip 단독 22/25 · (c)+(a) 22/25(slip 중앙 -0.05) · (c)+(b) 22/25. noslip(b)은 slip 비 -0.24 로 플러그가 TCP 보다 더 움직이고 joint frictionloss 에도 작용(7.0N 에서 0.000mm vs 0.14mm)해 배제. 마찰 μ=1 불변(>2 편법 없음), 이탈 힘 7.316N 불변. 검증자가 5배치로 "각 옵션 단독 5/5" 라 한 것은 25배치에선 재현되지 않음.
- **파지 불가 배치 제외**: 남는 실패 배치(2·6·13)는 slip 이 아니라 파지 직전 열린 moving_jaw 가 shoulder 링크와 최대 7.8mm 겹치는 자세 → self-check [6] 은 무관통 자세만 대상으로 "전부 FULL" 을 요구(비율 임계보다 엄격).
- **"jaw 가 후드 윗면에 얹힘" 음성 대조군은 넣지 않음**: 윗면 겨냥은 법선 22~26N 누르기라 μ=1 쿨롱 한계가 7.2N 보유력보다 커서 끌면 빠지는 게 물리적으로 맞음(수정 후 11/25). 1mm 위 겨냥은 0/25·최대 0.54mm 로 0.5mm 한계에 너무 가까워 flaky. 실제 완화책 = 비축 하중 시 커넥터 binding 모델링(남은 이슈).
- **expert 파지**: S1 교훈대로 TCP 가 아니라 **jaw 접촉점 중점**(`GRASP_LOCAL`, 핀치 접촉점 실측 캘리브)으로 겨냥. 매 하강·당김 단계 IK 재계산. 존 근단은 그리퍼 축을 팔 평면 안에서 0~30° 기울인 파지를 탐색(jaw 개폐축 ↔ 보드 y 어긋남 ≤15°). 무관통 자세가 없으면 실행하지 않고 unreachable/margin_blocked 사유 기록. 파지점 이동 9mm 후보는 실행 grasp_miss(1004·1015) 로 제거.
- **학습 epoch 42 (S1 은 30)**: 야간 드라이버의 `train_completed()` 는 마지막 metrics 줄 epoch == `COP_EPOCHS:-42` − 1 을 요구하고 야간 호출에 `COP_EPOCHS` 가 없다. 30epoch 로 돌리면 야간마다 "이상종료 → 재학습" 판정됨(가짜 metrics 로 실측: epoch 41 = 완료 승격, epoch 29 = 재학습). 그래디언트 스텝은 42×2003 ≈ 84k 로 S1(30×903 ≈ 27k)보다 적지 않음.
- **측정 success_rate = 부분성공**: 로드맵 Phase 4 완료 기준 "시뮬 분리 부분성공 50%" 와 드라이버 TARGET_RATE 0.50 이 같은 단위가 되도록. 완전분리 full_rate 는 항상 병기.

## 5. 남은 이슈
1. **존 근단 도달불가**: PCB x<0.19 에서 2/19(0.11), 0.19~0.22 에서 23/27. unreachable·margin_blocked·approach_blocked·jam 모두 shoulder 링크 기하 간섭이 뿌리. expert 새 시드 0.75 는 합격선 경계값이다.
2. **jam 원인 오분류(게이트 3 불합격)**: 코드·로그의 jam 사유 설명(서보 토크 한계)을 "shoulder 링크 역방향 접촉" 으로 고쳐야 함. 코드 수정은 이번 범위 밖이라 미반영.
3. **데이터셋 근단 편향**: 1차 시도 성공만 저장 → 100ep 중 x<0.19 는 3ep. ACT 정책도 근단에서 약할 가능성이 크고, 4-seed 측정에서 근단 배치가 나오면 실패로 잡힐 것(측정 전이라 미확인).
4. **야간 측정 300s timeout 위험(미검증)**: hermes `cop_sim_env.py` 가 드라이버를 timeout=300 으로 부르고 측정은 그 안에서 동기 실행. 실패 rollout 1회 스모크 10.4s → 40회 전부 최대 프레임이면 ≈416s + 모델 로드 > 300s. 초과 시 `cop_measured.marker` 미기록 → 매일 재측정 반복. S1 드라이버 측정은 164s 였음. hermes 스크립트라 이번에 변경하지 않음.
5. **top 뷰 팔 가림**: 홈 자세에서 후드가 top 에 완전히 가려지는 리셋 14/200, 가시 <50% 64/200. closeup 에는 항상 보임.
6. **모델 근사**: 보유력 7.2N 은 규격 대역 추정값(실측 아님), 잭스크류 미체결 가정, 포트 간격 36mm 목측, 사다리꼴 쉘·백쉘 박스 근사, 케이블은 시각 전용(장력·강성 없음), 비축 하중 시 binding 미모델.
7. **h264 측정 간극**(S1 과 동일): 학습 데이터는 h264 왕복 프레임, rollout 은 raw 렌더.
8. **마커 복귀 주의**: RS232 marker 승격 후 `logs/cop_dataset_target` 만 `data/episodes_s1` 로 되돌리면 시그니처 불일치로 S1 을 `--no-resume` 재학습해 `checkpoints/act_s1_sim` 을 덮어쓸 수 있음. 되돌릴 땐 scratchpad 백업(`cop_dataset_target.prev`·`cop_trained_on.marker.prev`=`episodes_s1:1785931493`·`cop_measured.marker.prev`=`episodes_s1:1786060554`)을 함께 복원.
9. 실기 프레임에서 플러그가 꽂힌 포트 위치 확정 필요(3절).

## 6. 다음 단계
- ACT 학습(pid 31176) 완주 대기 → 9/11·9/12 23:00 야간은 STAGE=학습중 hold 예상, 9/13 23:00 야간에서 marker 승격(stage 2.5) + 4-seed 측정(stage 5, `render_act_rollout_rs232.py`) 예상. 첫 체크포인트 epoch_0009 는 착수 약 8h 후.
- 측정 시 부분성공·완전분리 둘 다 보고하고, 실패를 PCB x 구간별로 나눠 근단 편향(이슈 3)을 확인.
- 야간 측정 wall time 확인 → 300s 초과 시 hermes 쪽 timeout 조정 여부를 사용자와 결정(이슈 4).
- jam 사유 문구 정정(이슈 2), 근단 파지 전략(다른 접근 자세 또는 근단 배치를 과제 불가로 명시) 검토.
- W2: RS232 DR 합성 + 재학습. 실기 협업: 보유력 실측(당김 저울)·포트 간격·꽂힌 포트 위치.
