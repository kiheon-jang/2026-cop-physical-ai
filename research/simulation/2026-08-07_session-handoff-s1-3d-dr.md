# 세션 인수인계 — 2026-08-07 (W3 측정기 → 크론 S1 전환 → 대시보드 B메인 3D 재설계 → DR 강건성)

> 이전 핸드오프: `research/simulation/2026-08-06_session-handoff-s1-alignment.md` (그 §4 우선순위대로 이어받아 진행함).
> 이 문서 = 이번 세션 전체를 **누락 없이** 기록. 새 세션이 이대로 이어받으면 됨.

---

## 0. 지금 상태 (재시작 시 가장 먼저 확인)

| 항목 | 상태 | 확인 방법 |
|------|------|-----------|
| **S1 정책** | `checkpoints/act_s1_sim/epoch_0029` (30ep 완주, 최종 loss 0.0133). **4-seed 공정추정 0.925** | `ls checkpoints/act_s1_sim/` |
| **야간 크론** | **S1 전환 완료.** target=`data/episodes_s1`, 정상흐름 = stage5 측정 1회 → stage6 완료/유지 0.925 | 아래 §3 마커 |
| **진행 중 백그라운드** | **없음.** (DR 3축 + ablation 3종 측정 전부 완료) | — |
| **브라우저 페인** | 이 세션 내내 **wedge**(서브에이전트 탭 난립, file://·claude.ai 차단). **BUT 헤드리스 Chrome으로 WebGL 렌더·스크린샷 됨** → §5 참조 (교착 해소 도구) | — |
| **대기 = 사용자 결정** | ① ② DR 재학습 착수 여부 ② 스토리·플레이그라운드 실경험 착수 ③ 9월 Obsidian 보고서 "정밀삽입" 문구 ④ 커밋 여부 | — |

**커밋 안 함** (이번 세션 내내 사용자 지시 없어 커밋 0. 브랜치=main).

---

## 1. 이 세션에서 한 일 (전부)

### 1-1. W3 측정기 — S1 rollout 측정 스크립트 (이전 §4.2, 완료)
- **신규 `scripts/render_act_rollout_s1.py`** — `render_act_rollout.py`의 S1 판본.
- 재사용: `train_act.build_model`(가중치 로드) + `sim_pcb_reset.PcbResetTwin`(환경 불변 — 버튼·스프링·존 안 건드림).
- **관측 계약(중요)**: 2카메라 `observation.images.{top,closeup}` + `observation.state`=qpos[:6]. **이미지 상하반전 없음**(S1 수집기 `sim_pcb_reset.render`가 raw 저장 — pick-place의 `[::-1]`와 다름). 정책 액션당 물리 17스텝(`DATA_SAMPLE_EVERY`, 수집과 동일). `cfg.camera_keys=["top","closeup"]` 강제(env 무관하게 2카메라 체크포인트와 형상 일치).
- **성공 판정 = LED latch**(`twin.led_on()`, 실기 P1 녹색LED와 동일 계약). 물리 스텝은 `twin.step()`(latch 갱신).
- **4-seed 프로토콜**: seeds 42/7/123/2026. seed42=nominal.
- **결과: 4-seed 0.925** (per-seed 0.9/0.9/1.0/0.9). 실패=존 구석 기하 도달불가(expert 잔여와 동일).
- 산출물: `rollout_summary_s1[_seedN].json`(4개) + `history/*_traj.json`(**nominal seed42만** — dedupe·리플레이=영상 seed 일치) + `history/*.json`(4 seed 요약) + 영상 `inference_act_s1_sim_epoch_0029_20260806.mp4`(track2).
- **정직 고지(측정 방법론)**: 학습 데이터셋은 h264 영상(수집기 `use_videos=True`)이라 백본이 본 프레임은 인코드/디코드 거쳤지만 측정은 무손실 raw 렌더 — pick-place 측정기와 동일 방법론, docstring에 명시.
- **3-lens 어드버서리 리뷰 통과**(환경불변 CLEAN, critical 0).

### 1-2. 04:04 killer 확증 종결 (이전 §4.1, 완료)
- 8/5밤 S1 학습(30ep)이 04:04 관통해 완주(epoch_0019 06:11·epoch_0029 09:37·loss 0.0133) → **가설 확정**(범인=`ai.hermes.autoupdate` launchd 04:00 → gateway kickstart → 프로세스그룹 SIGKILL, fix=`start_act_train.sh` start_new_session).
- `agent/external-dependencies.md`에 종결 표기 추가.

### 1-3. 크론 드라이버 S1 전환 (이전 §4.3, 완료)
- **`scripts/cop_pipeline_advance.sh`에 `IS_S1` 분기 추가**(+21/-2):
  - CKPT_DIR = `checkpoints/act_s1_sim`(규칙상 `act_s1`이 되는데 실제 학습경로는 `act_s1_sim` — 특수분기로 교정).
  - 측정 스테이지 = `render_act_rollout_s1.py`(pick-place는 `render_act_rollout.py`).
  - 학습 스테이지 = `COP_CAMERA_KEYS=top,closeup` + `COP_DATASET_REPO_ID=local/pcb_reset_sim` export(2카메라 계약).
  - 수집 스테이지 = S1이면 **보류**(합성 100ep 고정, pick-place 수집기로 채우면 오염).
  - COP_SCENE 케이스에 `*s1*` 추가(측정기는 twin 자체로드라 참고용).
- **`render_act_rollout_s1.py` 최종 JSON에 `"success_rate": fair` alias 추가**(드라이버 stage6 grep 호환).
- **전환 상태 세팅**: `logs/cop_dataset_target`=`data/episodes_s1`, `logs/cop_trained_on.marker`=`episodes_s1:<info.json mtime>`(사전세팅으로 epoch_0029 재학습 방지 = 진짜 사실 기록).
- **드라이버 수동 2회 검증**: 1회차 STAGE=측정(0.925) → measured 마커 세팅, 2회차 STAGE=완료/유지 0.925.
- fresh-context 리뷰: 정상 야간운영 중 데이터손실 경로 0(재학습 가드 정확·안정: episodes_s1 gitignore→mtime 불변).
- **LOW 리스크(미조치, 사용자 판단)**: `checkpoints/act_s1_sim/epoch_0029` 백업 없음. 수동으로 마커 삭제/데이터 재생성 시에만 재학습 트리거(야간엔 안 터짐). 원하면 `cp -R epoch_0029 epoch_0029_measured_0.925.bak`.
- `agent/cron-jobs.md`에 S1 분기·전환 기록.

### 1-4. 대시보드 홈 인터렉티브 재설계 (이전 §4.5 — **이 세션의 큰 축**)

**a) 리서치**: healthchecks.io 첫화면 = 애니메이션 파이프라인 플로우(잡→허브→알림 초록체크 흐름) + 상태색상(초록/주황/빨강) + 밝고친근. 유사: Linear(다크프리미엄)·Stripe/Vercel·Inngest/Temporal/Trigger.dev(파이프라인 애니, CoP에 직결).

**b) 4개 시안 생성**(전부 자립형 HTML, `dashboard/_sian_previews/`):
- A `A_pipeline.html` 살아있는 파이프라인(healthchecks 라이트)
- B `B_missioncontrol.html` 미션컨트롤(다크 프리미엄) ← **사용자 선택**
- C `C_scrolly.html` 스토리 스크롤(잡지)
- D `D_playground.html` 플레이그라운드(파스텔 장난감)
- 비교 갤러리 아티팩트 `gallery.html`(srcdoc iframe 4개).

**c) 사용자 결정**: **B를 메인** + 스토리(C)·플레이그라운드(D)는 **버튼으로 포함**(하나도 안 버림). 톤=B 다크. "3단계 여정보기"·"성과지표" 버튼 → **"스토리"·"플레이그라운드" 버튼 대체**. C·D는 B톤으로 통일 예정(미착수).

**d) 실기 팔 사양 확정**(사용자 정확도 요구): 우리 구매유닛 = **SO-101, `hdel_iot_01` 캘리브 실파일**(`/Volumes/MARK_DATA/dev/soarm_lerobot/calibration/robots/so_follower/hdel_iot_01_follower_arm.json`). 6모터 ID 1~6(shoulder_pan/lift/elbow_flex/wrist_flex/wrist_roll/gripper), Feetech STS3215. 링크 실비율(sim `SO-ARM100/Simulation/SO101/so101_new_calib.xml`): upper_arm~11.3cm·lower_arm~13.5cm·wrist~6cm. **그리퍼=단일 이동턱**(`moving_jaw_so101_v1` 흰 위턱 + 고정 검은 갈고리 아래턱, 비대칭). 참조사진 `models/SO-ARM100/media/SO101_Follower.webp`.

**e) 히어로 카피 확정**(사용자 제공, 오타만 정리, 쉼표 줄바꿈):
```
헤드라인: 엘리베이터 제어반을, 로봇이 점검하기 위한 첫걸음. / 로봇팔이 손끝을 배웁니다.
서브(5줄, <br>): 가상 환경(MuJoCo)에서 매일 학습 데이터를 쌓고, / 익힌 데이터를 실제 로봇팔로 옮깁니다. /
병행하여 실기기에서 모션 학습을 통해 데이터를 쌓아 정확도를 높입니다. /
로봇팔이 제어반의 전원 버튼을 눌러 리셋하고, / 꽂혀 있는 케이블을 빼는(분리) 것을 목표로 합니다.
```

**f) 3단계 용어 변경**(사용자): RS232 = "정밀 삽입/±0.5mm/꽂기" → **"케이블 분리(꽂힌 케이블 빼기/제거)"**. 로봇이 꽂혀있는 걸 빼는 동작. 수정 18곳: `dashboard/build.py`(5) + `dashboard/template.html`(4) + `research/simulation/PHASE_ROADMAP.md`(5) + `B_main_v2.html`(4). 라이브 대시보드 재빌드 반영. **남은 1건 = 9월 Obsidian 활동보고서**("정밀 삽입 시뮬 데이터 합성 (300ep)", 소스=`~/Documents/03 Areas/회사문서/CoP_PhysicalAI/CoP_*_활동보고서.md`, **사용자 명의·PARA read-only → 미수정, 사용자 결정 대기**).

**g) 텔레메트리 = 실데이터 재생**(사용자 확정: 학습은 새벽 배치라 라이브 불가 → 여태 진행분 루프 재생):
- 우측 콘솔 로그 = 진짜 31에폭 학습로그(`logs/act_train_metrics.jsonl` episodes_s1, loss 74.5→0.013) 재생, loss sparkline, 4-seed sparkline, "재생(여태 학습분 반복·실데이터)" 라벨.
- 팔 움직임 = 진짜 rollout 궤적(`history/*_traj.json` epoch_0029 nominal) 재생, LED 46프레임째 점등.
- **명확화**: 히어로 3D는 "결과 재생"(녹화 궤적 시각화)이지 정책 실시간 아님. 진짜 학습·판단은 카메라 기반.
- 임베드 데이터: `real_data.json`(31에폭+4관절궤적) → 나중에 3D용 `real_traj_full.json`(6관절 120f)로 확장.

**h) 3D 팔 고도화**(사용자: "3D 애니메이션급, 색상 B톤, 회전/확대 확인"):
- **1차 시도 실패**: 절차적 프리미티브 팔 + FK sign/offset **추측** → 관절이 뱀처럼 튐·허공 뜸·버튼 과대(반지름 0.014). 원인=렌더 못 보고 추측.
- **교착 해소**: **Chrome 헤드리스로 WebGL 렌더·스크린샷 가능** 발견(§5) → 이후 눈으로 보며 수정.
- **근본 해결**: 추측 폐기, **작동하는 3D 리플레이(sim3d) 방식 그대로 이식** — `web3d_chain.json`(실모델서 export한 바디트리+관절축+메시), MuJoCo(w,x,y,z)→THREE 쿼터니언, Z-up→Y-up root만 -90°X, `pivot.quaternion.setFromAxisAngle(axisV, q[qposadr])`(sign/offset 없음), b64 메시 디코드, 오빗(az/el/dist). **실측 치수**(pcb_reset_scene.xml): 보드 0.15×0.15×0.01·**버튼 원통 r0.004 h0.006(작음!)**·LED 0.008³. 다크톤 재질만 히어로용 교체.
- **헤드리스로 검증 완료**: 팔=진짜 SO-101 형상 보드 위 서서 하강, 흰 그리퍼가 작은 빨간 버튼 정확히 누름 + 초록 LED 점등, 여러 프레임 자연스러운 로봇동작. (내 눈 확인 스크린샷 `/tmp/verify_3d.png`, `/tmp/arm_zoom.png`.)
- **카운트업 버그 clamp**: `p=Math.max(0,Math.min(...,1))` — 헤드리스 가상시간이 rAF now를 start 이전으로 줘서 -410%/-379% 나온 것(실브라우저선 정상일 것), 방어적 clamp.
- **정직 고지**: 파일 1.48MB(Three.js 618KB+체인 763KB 인라인). swiftshader 소프트렌더 느림(프레임 1~2분), 실GPU 즉시. 헤드리스 virtual-time에선 부팅오버레이(#boot) 페이드 안 됨(검증 땐 임시 `#boot{display:none}` 사본 사용, 원본 미변경).

**i) 산출/조립**:
- `B_main_v2.html`(46KB) = 마커 원본(`<canvas id="hero3d">` + `<!--INJECT:THREEJS/REALTRAJ/ARM3D-->` + 텔레메트리·게이지·버튼·카피). **텔레메트리/카피는 절대 건드리지 말 것**, 팔 캔버스만 교체.
- `arm3d.js`(13KB) = 체인기반 3D 렌더 모듈(THREE+REAL_TRAJ+WEB3D_CHAIN 전역 사용).
- `three.r152.js`(618KB) = template.html에서 추출·검증(node로 THREE r152 확인).
- `real_traj_full.json` = 실측 6관절 궤적.
- `build_b_main_3d.py` = 조립 스크립트(마커에 three.js·chain·traj·arm3d 주입, **손복사 아닌 스크립트** — 618KB 재현 위험 회피).
- `B_main_3d.html`(1.48MB) = 최종 자립형.
- `B_main_v2_artifact.html`(1.45MB) = 아티팩트용 srcdoc iframe 래퍼.

### 1-5. 시뮬 유효성 Q&A (사용자 질문)
- Q: 실기는 카메라로 버튼 확인해서 누르는 플로우인데 지금 시뮬 의미 있나?
- A: **의미 있음. 정책이 카메라 기반**이라. ACT 입력=2카메라영상+관절상태, 버튼은 매 에피소드 15×15존 무작위(정책은 버튼좌표 못 받음, 카메라로만 찾아야 함) → 실기 플로우 그대로. expert는 버튼좌표 알지만 학습된 정책은 카메라만 봄(모방학습). 카메라도 실기정렬(top C920/closeup Realtek·640×480·동일스키마). **한계=시뮬 렌더영상≠실카메라(sim2real 비주얼갭)** → 대응=DR + 실기트랙 병행.

### 1-6. DR 강건성 측정 (① 완료 — 재학습 없음)
- **`render_act_rollout_s1.py`에 `--dr`/`--dr-axes` 추가**: `sim_domain_randomization`(조명/마찰/카메라노이즈 3축) 배선. 매 rollout `restore_baseline`→`randomize_scene`→`mj_setConst`→노이즈를 top+closeup 렌더에 적용. **환경치수 불변**(버튼·존 안 건드림, 조명/마찰/카메라만·복원). DR rng는 존 rng와 분리(버튼배치=nominal 동일). 별도 파일 `rollout_summary_s1_dr[_axis][_seedN].json`, 영상·3D traj 스킵.
- **결과 (전부 4-seed)**:

| 조건 | 4-seed 성공률 | 낙폭 |
|------|------|------|
| nominal(무섭동) | **0.925** | — |
| DR 카메라 노이즈만 | **0.625** | −30%p |
| DR 조명만 | **0.65** | −27.5%p |
| DR 마찰만 | **0.725** | −20%p |
| DR 3축 동시 | **0.45** | −47.5%p |

- **판정**: 범인 1·2위=**시각(카메라+조명)**, 마찰은 덜. 정책이 **clean 시뮬 영상 과적합** → sim2real 시각갭에 정확히 취약. **② DR 재학습 정당화됨**(①이 필요성 판별 = 필요).
- 정직: 표본 작음(seed당 10 rollout, 카메라 0.4~0.8 편차). 0.45는 DR범위 넓어 worst-case-ish. 핵심신호=낙폭·시각축.

---

## 2. 파일 변경 전수 (이 세션)

**신규**:
- `scripts/render_act_rollout_s1.py` — W3 S1 측정기 (+ DR 경로)
- `dashboard/_sian_previews/` (디렉터리 전체): `A_pipeline.html` `B_missioncontrol.html` `C_scrolly.html` `D_playground.html` `gallery.html` `B_main_v2.html` `arm3d.js` `three.r152.js` `real_data.json` `real_traj_full.json` `build_b_main_3d.py` `B_main_3d.html` `B_main_v2_artifact.html`
- `research/simulation/inference_progress/rollout_summary_s1*.json` (nominal 4 + DR 3축 4 + ablation 12 = 20개) + 대응 `history/*.json`(요약) + `history/*_traj.json`(nominal만) + `inference_act_s1_sim_epoch_0029_20260806.mp4`
- 이 문서

**수정**:
- `scripts/cop_pipeline_advance.sh` — IS_S1 분기
- `agent/external-dependencies.md` — 04:04 종결
- `agent/cron-jobs.md` — S1 분기·전환
- `dashboard/build.py` — S1 비교표 라벨(4), 케이블 분리(5), (Phase4 정의는 PHASE_ROADMAP서)
- `dashboard/template.html` — 3D 리플레이 S1 정책브랜치(sim3dApplyFrame ep.pcb 가드), 2단계 스토리카드 s1fair 92.5%, 케이블 분리(4)
- `research/simulation/PHASE_ROADMAP.md` — 케이블 분리(5)

**메모리 갱신** (`~/.claude/projects/-Volumes-MARK-DATA-dev-2026-cop-physical-ai/memory/`):
- `real-track-alignment-2026-08.md` — W3·크론S1·DR측정·ablation 전부
- `dashboard-redesign-sian-2026-08.md` — 신규(시안·B메인·용어·3D)
- `MEMORY.md` — 인덱스 추가

---

## 3. 라이브 파이프라인 상태 (마커)

```
logs/cop_dataset_target   = data/episodes_s1
logs/cop_trained_on.marker  = episodes_s1:1785931493   (info.json mtime — 재학습 방지)
logs/cop_measured.marker  = episodes_s1:1785976636   (epoch_0029 sig — 측정 완료)
```
야간 크론(cop_sim_env.py 23:00 → cop_pipeline_advance.sh) 정상흐름 = STAGE=완료/유지, 성공률 0.925 보고. **주의: 위 3파일이 gitignore 안일 수 있음 — 새 세션서 `cat`으로 확인.**

---

## 4. 아티팩트 URL (사용자 브라우저용 — claude.ai 페인 차단이라 발행만)

- **시안 비교 갤러리** (4종 탭): https://claude.ai/code/artifact/adf5f0b5-806d-4b25-87ff-131005cd29f4
- **메인(B) 3D** (최종, 실기팔+실데이터+3D): https://claude.ai/code/artifact/af9f5dab-7a32-4e45-8dbf-613e277ce932
- 갱신법: 같은 파일경로(`dashboard/_sian_previews/B_main_v2_artifact.html`)로 재발행 → 같은 URL 유지. 새 세션이 아니면 `url` 파라미터로 지정.

---

## 5. ⚠️ 헤드리스 Chrome 렌더 검증 (이 세션 핵심 도구 — 반드시 인계)

브라우저 페인이 wedge라 file://·claude.ai 렌더 안 됨. **BUT Chrome 헤드리스로 WebGL 렌더+스크린샷 됨** — 3D/애니 검증의 유일한 길. 명령:
```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CHROME" --headless=new --disable-gpu --enable-unsafe-swiftshader \
  --use-gl=angle --use-angle=swiftshader --hide-scrollbars --force-prefers-reduced-motion \
  --window-size=1240,880 --virtual-time-budget=25000 \
  --screenshot=/tmp/chk.png "file:///path/to/file.html"
# 그 다음 Read /tmp/chk.png 로 눈으로 확인. PIL로 크롭 확대 가능.
```
- swiftshader 소프트렌더라 프레임당 ~1~2분(shadow map). `--force-prefers-reduced-motion`으로 정지프레임(누른자세+LED) 뽑으면 빠름.
- virtual-time에선 카운트업/부팅오버레이 아티팩트 → 검증 시 임시 `#boot{display:none}` 사본 쓰거나 clamp된 현 버전 사용.
- **교훈: 3D/애니는 절대 추측으로 만들지 말고 이 명령으로 보며 고칠 것.** (1차 절차적 FK 추측이 뱀꺾임 낸 원인.)

---

## 6. 다음 할 일 (우선순위 — 사용자 결정 대기)

1. **② DR 재학습** (사용자가 ①→②로 가는 중) — DR 강건성 0.45가 정당화. 처방: 수집기 `samples/training/sim_pcb_reset_collector.py`에 DR 훅(조명/마찰/카메라, 최소 시각 2축) 추가 → DR로 `episodes_s1` 재수집(또는 학습 augment) → 재학습(~반나절, epoch_0029 대체) → `--dr`로 강건성 재측정(0.45가 얼마나 오르나). **무겁다 — 사용자 착수 지시 대기.**
2. **스토리(C)·플레이그라운드(D) B톤 통일 + 버튼 연결** — 메인 방향 승인됨. 플레이그라운드에 실궤적 재생 모드(가능 확인됨: `real_traj_full.json`). C는 크림→다크 리스킨, D는 파스텔→다크.
3. **메인 3D 최종 확정 → 실제 `dashboard/template.html` 홈 라우트 적용** (지금은 `_sian_previews` 프로토타입/아티팩트. 사용자 OK 시 라이브 홈 통합).
4. **9월 Obsidian 활동보고서 "정밀삽입" 문구** — 사용자 명의·read-only, 결정 대기.
5. **커밋** — 세션 내내 커밋 0. 지시 대기.
6. **epoch_0029 백업** (§1-3 LOW 리스크) — 원하면 `cp -R`.
7. **omen 핸드오프** (이전 §4.4) — 합성셋 전달 + lerobot 0.6.1 로드 스모크. 협업채널 필요.

---

## 7. 알려진 제약 / 주의

- **환경 불변 원칙(사용자 강지시)**: S1 씬 버튼치수·스프링·존은 실기 기준 — 성공률 위해 바꾸지 말 것. DR도 조명/마찰/카메라만 흔들고 버튼·존 불변·복원.
- 카메라 이름 계약 top/closeup 고정(실기 camswap 사고 전례).
- Mac lerobot 0.5.1 ↔ omen 0.6.1 API 차이. 데이터 v3.0 양쪽.
- `data/episodes_s1` gitignore(대용량) — 사이드카 포함 재생성 가능.
- 브라우저 페인 wedge(이 세션) — 검증은 §5 헤드리스로. 새 세션은 페인 정상일 수 있음(먼저 테스트).
- 3D 파일 1.48MB — 실GPU 즉시, 헤드리스만 느림.
- DR 결과는 **재학습 아님**(측정만) — epoch_0029 그대로. DR summary는 별도 파일(nominal 0.925 불변).

---

## 8. 명령어 재현

```bash
# S1 rollout 측정 (4-seed nominal)
.venv/bin/python3 scripts/render_act_rollout_s1.py --device cpu

# DR 강건성 (3축)
.venv/bin/python3 scripts/render_act_rollout_s1.py --dr --device cpu
# DR 축별 ablation
.venv/bin/python3 scripts/render_act_rollout_s1.py --dr --dr-axes camera --device cpu   # light / friction / camera

# 크론 드라이버 수동 실행 (S1 상태 확인)
bash scripts/cop_pipeline_advance.sh

# 대시보드 재빌드
.venv/bin/python3 dashboard/build.py

# 메인 3D 조립 (수정 후 재조립)
python3 dashboard/_sian_previews/build_b_main_3d.py   # 있으면; 없으면 §1-4 i 참조

# 헤드리스 3D 검증 → §5
```

---

**이번 세션 요약 한 줄**: W3 측정기(S1 0.925)·04:04확증·크론S1전환 마무리 + 대시보드 홈을 B(미션컨트롤 다크)로 재설계(실기팔 3D·실데이터재생·케이블분리·쉼표줄바꿈) + DR 강건성 측정(0.45, 시각 과적합 확인, ② 재학습 정당화). 다음=② 재학습 or 스토리/플레이그라운드 착수, 사용자 결정 대기.
