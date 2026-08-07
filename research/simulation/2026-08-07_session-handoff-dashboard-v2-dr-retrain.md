# 세션 인수인계 — 2026-08-07 (대시보드 B 실적용 v2 + RS232 용어 전면정합 + ② DR 재학습 착수)

> 이전 핸드오프: `research/simulation/2026-08-07_session-handoff-s1-3d-dr.md` (이 세션 시작점 = W3측정기·04:04확증·크론S1·대시보드 B 프로토타입·DR 강건성 0.45 측정까지).
> 이 문서 = 그 이후 이 세션 전부를 **누락 없이** 기록. 새 세션은 이대로 이어받으면 됨.
> 관련 메모리: `dashboard-redesign-sian-2026-08.md`, `real-track-alignment-2026-08.md` (둘 다 이 세션 반영 완료).

---

## 0. 지금 상태 (재시작 시 가장 먼저)

| 항목 | 상태 | 확인 |
|------|------|------|
| **② DR 재학습** | **가동 중** — 수집 100/100 완료 → 학습 **epoch ~8/30**(loss 0.097, nominal 궤적과 일치, 정상). 드라이버 디태치 ALIVE. **ETA 오늘 밤 ~21시**. | `cat logs/dr_retrain.status` / `tail logs/dr_retrain.log` / `kill -0 $(cat logs/dr_retrain.pid)` |
| **대시보드** | **B(미션컨트롤) 실적용 완료**. 서버(hermes-mark localhost:4001)가 라이브 서빙 중. 이 세션 커밋 10개 전부 반영(chokidar 자동재로드). | `curl -s localhost:4001/projects/cop-physical-ai/ \| grep initHero3D` |
| **RS232 용어** | **전면 "케이블 분리" 정합 완료** — repo + Obsidian vault 22+파일. | 아래 §3 |
| **git** | main, 미커밋 소스 0 (SO-ARM100 내장repo·생성물만 untracked). 이 세션 10커밋. | `git log --oneline 96da450..HEAD` |
| **DR 측정** | **대기** — 학습 완료 후 수동 측정으로 DR 0.45 개선폭 확인. | 아래 §5 |

**핵심 커밋 10개 (1e5aae9 → 335b694)**:
```
335b694 Playground 마우스조종(스크럽+클릭) + Overview 로그박스제거(한화면)
55995bf Playground = 진짜 3D 실기팔(SO-101) + 한화면
ff91e34 Overview 한화면 + Story로 섹션이동 + 스토리 결선→분리 + 플레이그라운드 멈춤수정
c2fcdc8 홈 3D 복구 + 스토리/플레이그라운드 고유화(중복 제거)
84adf15 [용어] RS232 옛명칭(연결/Insertion/꽂기/통신학습) → 케이블 분리 확장정합
a47ceff 스토리(C)·플레이그라운드(D) B톤 통일 + 라우트 연결
f293b7b [용어] RS232 결선/정밀삽입 → 케이블 분리 정합(현행 문서)
2fa144a 홈 라우트에 시안 B(미션컨트롤 3D) 실적용
6eff7cc [시뮬] ② DR 재학습 착수 — 수집기 DR훅 + 드라이버
1e5aae9 홈 B(미션컨트롤) 3D 재설계 + DR 강건성 측정
```

---

## 1. ⚠️⚠️ 서버 서빙 근본원리 (버그 재발 방지 — 반드시 숙지)

**hermes-mark 서버(bun, `localhost:4001`)가 `dashboard/template.html`을 직접 서빙한다. build.py 산출물 `dashboard.html`은 서빙 안 한다.**
- 코드: `/Volumes/MARK_DATA/dev/hermes-mark/server/readers/projects-cop.ts` `loadTemplate()` + `injectDocsViewer()` — **DOCS 마커만** 치환. chokidar로 template.html+data.json 워치 → 변경 시 자동 재로드(게이트웨이 재시작 불필요).
- 서버모드는 DATA도 비동기: 빈 placeholder로 로드 → `/api/projects/cop-physical-ai/data` fetch + WS 갱신.
- **결과**: build.py 마커 주입(`/*__ARM3D_JS__*/` 등)은 서버뷰에 **안 먹음**. 8/7 사용자 리포트(오버뷰 3D 안뜸·스토리/플레이그라운드 빈화면)의 근본원인.
- **해결(현재 방식)**: `dashboard/bake_embeds.py`가 **arm3d.js를 template에 인라인 + 스토리(C)를 iframe srcdoc에 베이크**. → 서버가 template 서빙하면 3D·스토리 실내용 나옴.
- **규칙**: `arm3d.js` 또는 `C_scrolly.html` 수정 시 반드시 `.venv/bin/python3 dashboard/bake_embeds.py` 재실행 → template 갱신 → 서버 chokidar 자동반영 → 사용자 **강력새로고침(Cmd+Shift+R, 캐시)**.
- 서버모드 3D는 DATA(web3d) 비동기라 `initHero3D`/`mountArm3D` 멱등+재시도로 대응(renderBmcHome이 DATA 준비 후 재호출; setRoute가 12회 재시도).

---

## 2. 대시보드 아키텍처 현황 (뷰별)

**공통**: 라이브 홈은 `dashboard/template.html`의 `#view-home` = **시안 B(미션컨트롤 다크)**. 레거시 관제탑 홈은 `#home-legacy hidden` 보존(drawHeatmap 등 null참조 방지). CSS 전부 `.bmc-home` 스코프 + 키프레임 `bmc-` 접두(SPA/타라우트 격리). 진짜 3D 팔 = `arm3d.js`(web3d_chain 실 SO-101 메시, `D.web3d.chain`+`policy_history` 라이브).

- **Overview(`view-home`, 라우트 home)** = **한 화면**. 히어로(카피 + 3D콘솔 `#hero3d` + 칩)만. 로드맵/성과지표/야간파이프라인 **섹션 제거**(사용자: 한화면), 로그박스(statstrip+train.log)도 **제거**(작은 랩탑 760h서도 스크롤 없이 딱). D-day 등 스칼라는 `D.business_kpi` 라이브.
- **Story(`view-story`, 라우트 story)** = **기존 스크롤 내러티브 컨셉 유지**(사용자 명시 "한화면 아님"). `<iframe id="story-frame">` srcdoc에 `C_scrolly.html` 베이크. 내용: 스크롤텔링(집기→버튼→케이블분리 SVG 모프, **그레이메탈 팔**) + **성과지표 + 야간파이프라인 섹션**(사용자가 Overview→Story 이동 요청, 복원됨). 3단계 문구 "케이블 분리/뽑기"(결선/삽입/꽂 전부 수정). ⚠️ 팔은 스타일라이즈드 2본 SVG(그레이메탈 리컬러). 진짜 3D 아님(사용자 "생긴것만 맞춰"로 OK).
- **Playground(`view-playground`, 라우트 playground)** = **native 3D 실기팔 + 마우스 조종 + 한화면**. `<canvas id="play3d">` + intro + 카운터(`#play-count`)+힌트(`#play-hint`). `mountArm3D('play3d', {interactive:true, counterId, hintId})`. **마우스 좌우 = rollout 스크럽(팔 구동, 홈→버튼 누름), 클릭 = 눌림(LED on)+카운트**. 궤도(드래그회전/휠확대) **제거**(사용자: 회전/확대 아님). ⚠️ **스크럽 방식**(마우스X→궤적프레임)이지 팔끝 커서 정확추종(3D IK) 아님 — 사용자 확인 대기 항목.

**arm3d.js 멀티인스턴스**: `mountArm3D(canvasId, opts)` — 캔버스 파라미터·per-canvas flag(`__arm3d_<id>`). `opts`: `frameId/ledId/playId`(라벨), `interactive`(스크럽+클릭·궤도off), `counterId/hintId`. `initHero3D`=#hero3d 래퍼(콘솔 라벨 연결). `buildHero(THREE,chain,RT,canvasId,interactive)`. `global.initHero3D`·`global.mountArm3D` 노출. **더 이상 D_playground(2D토이)·구 시안 C/D iframe은 Playground에 안 씀**(폐기).

**빌드/베이크 흐름**:
1. `arm3d.js`/`C_scrolly.html` 수정 → `bake_embeds.py`(arm3d 인라인 + C srcdoc 베이크) → template.html 갱신.
2. `build.py --no-json` → `dashboard.html`(정적, 서버 안씀·직접 열기용). build.py의 arm3d/srcdoc 주입은 **제거됨**(베이크가 대체).
3. 서버는 template.html chokidar 반영. 사용자 강력새로고침.

**시안 원본 파일**(`dashboard/_sian_previews/`): `arm3d.js`(3D 렌더 모듈·멀티인스턴스·interactive), `C_scrolly.html`(스토리, 리스킨+스트립+그레이팔+지표/파이프라인 복원), `D_playground.html`(2D 토이·**현재 미사용**, idle reduce게이트 제거됨), `A_pipeline.html`/`B_missioncontrol.html`/`gallery.html`(옛 시안·용어정합됨·미사용), `B_main_v2.html`/`B_main_3d.html`/`build_b_main_3d.py`/`three.r152.js`/`real_traj_full.json`(초기 B 프로토타입 자산).

---

## 3. RS232 용어 전면정합 ("결선/정밀삽입/연결/Insertion/꽂기/통신학습" → "케이블 분리")

**결정(사용자 8/7)**: RS232 태스크 = **분리(꽂힌 케이블 빼기/제거)**로 확정. "니가 바꿔도됨 관련부분 다 갱신."
**치환 규칙**(특정 구만; 바 "연결/삽입"은 일반어라 미변경): `HHT 자동 결선`→`HHT 케이블 자동 분리`, `정밀삽입/정밀 삽입`→`케이블 분리`, `케이블 연결`→`케이블 분리`, `RS232 Insertion`→`RS232 Disconnect`, `케이블 꽂기`→`케이블 분리`, `RS232 통신 학습`→`RS232 케이블 분리`, 잔여 `결선`→`케이블 분리`.
- **repo**(커밋 f293b7b·84adf15·c2fcdc8): dashboard/content(01-home·04-apps·spec-overview), scripts/daily-report/generate_daily_report.py, docs/(mail-template·form-guide·daily-reports/*.html·budget), 시안 A/B_mc/gallery/C/D, agent/HANDOVER.md, template/build.py/PHASE_ROADMAP.
- **Obsidian vault**(git 밖, 직접편집): **월별 활동보고서 8**(04·04_20260427·05·06·07·08·09·10) + **AI Wiki CoP 5**(AGENT_PROCESS·HANDOVER·PHASE_ROADMAP·2026-05/00_kickoff·2026-07/floor) + **hermes 리포트 2**(exec·team) + **예산집행 기안 1** = 16파일. `~/Documents/second-brain/` 하위.
- **⚠️ vault 편집 전 백업**: `/private/tmp/claude-501/.../c3557424-.../scratchpad/vault_backup_rs232/` — **scratchpad라 세션 클리어 시 소멸**. 되돌리려면 지금 확인. (vault 편집 자체는 영구·자연스러움 검증됨, 백업은 보험용.)
- **보존(소급수정 안 함)**: research/simulation handoff·kickoff·floor·closed-loop 노트(당시 용어·"결선 표기 제거" 결정 자체를 기록), build.py/PLAN.md 분류키워드(rs232가 이미 매칭). 전부 0 잔여 검증.

---

## 4. ② DR 재학습 (가동 중 — 오늘밤 완주)

**정당화**: DR 강건성 측정 결과 DR 3축 0.45 vs nominal 0.925(범인=시각 과적합, 카메라62.5·조명65·마찰72.5). ①이 필요성 판별 → ② 재학습.
**착수(커밋 6eff7cc)**:
- 수집기 `samples/training/sim_pcb_reset_collector.py`에 **env-gated DR훅**(`COP_COLLECT_DR=1`, `COP_COLLECT_DR_AXES=light,friction,camera`). 환경치수 불변(버튼/존 안건드림, DR rng 분리, expert 시연 무오염=버튼 실좌표 기반).
- 드라이버 `scripts/run_dr_retrain.sh`: DR 재수집(→`data/episodes_s1_dr`, gitignore) → cold-start 30ep 학습(→`checkpoints/act_s1_sim_dr`). **start_new_session 디태치**(04:04 killer 생존·세션종료 생존).
- **nominal 불변**: `checkpoints/act_s1_sim/epoch_0029`(0.925) 그대로 + 백업 `checkpoints/act_s1_sim/epoch_0029_measured_0.925.bak`.
- 라이브 마커(변경 안 함): target=episodes_s1, trained=1785931493, measured=1785976636.
**진행**: 수집 100/100(yield 92%) 완료 → 학습 epoch ~8/30(loss 0.097, ~20min/ep). 진행 = `cat logs/dr_retrain.status`(RUNNING train→DONE/FAILED).

---

## 5. 학습 완료 후 — DR 측정 (수동, 최우선 다음작업)

학습 끝나면(`logs/dr_retrain.status`=DONE, `checkpoints/act_s1_sim_dr/epoch_0029` 생성):
```bash
cd /Volumes/MARK_DATA/dev/2026-cop-physical-ai
# nominal + DR 둘 다 측정 (새 ckpt)
COP_CKPT_DIR=checkpoints/act_s1_sim_dr .venv/bin/python3 scripts/render_act_rollout_s1.py --device cpu       # nominal
COP_CKPT_DIR=checkpoints/act_s1_sim_dr .venv/bin/python3 scripts/render_act_rollout_s1.py --dr --device cpu  # DR 3축
```
- 비교: DR-재학습 ckpt의 DR 성공률이 **0.45 대비 얼마나 올랐나** + nominal(0.925) 유지 여부.
- ⚠️ render는 RUN_TAG="act_s1_sim" 고정 → 산출물이 **라이브 nominal summary(`rollout_summary_s1*.json`)를 덮어씀**. 라이브 대시보드 0.925 기록 오염 주의 — 측정 전 백업하거나 `--checkpoint` + 출력격리 고려.
- 개선되면 → `act_s1_sim_dr/epoch_0029`를 `act_s1_sim/epoch_0029`로 승격(백업 있으니 안전).

---

## 6. 이미지/리소스

- **아티팩트(claude.ai, 영구)**: 시안 갤러리 `https://claude.ai/code/artifact/adf5f0b5-806d-4b25-87ff-131005cd29f4` · 초기 B메인3D `https://claude.ai/code/artifact/af9f5dab-7a32-4e45-8dbf-613e277ce932`(같은 파일 재발행=URL 유지). ※ 현재 라이브는 이 아티팩트 아니라 서버 template.
- **스크린샷**: 이 세션 검증 스샷 전부 scratchpad(`.../c3557424-.../scratchpad/*.png`) = **세션 클리어 시 소멸**. 필요시 재생성(§7 헤드리스).
- **실기 SO-101 자산**: 3D체인 `dashboard/web3d_chain.json`(실 export, `D.web3d.chain`으로 주입). 실캘리브 `/Volumes/MARK_DATA/dev/soarm_lerobot/calibration/robots/so_follower/hdel_iot_01_follower_arm.json`. sim `SO-ARM100/Simulation/SO101/so101_new_calib.xml`. 참조사진 `models/SO-ARM100/media/SO101_Follower.webp`. 6모터 ID1~6(shoulder_pan/lift/elbow_flex/wrist_flex/wrist_roll/gripper), 단일 이동턱 그리퍼(흰 위턱+검은 갈고리).
- **체크포인트**: `checkpoints/act_s1_sim/epoch_0029`(nominal 0.925) + `.bak` + `checkpoints/act_s1_sim_dr`(학습중).

---

## 7. 명령어 재현
```bash
cd /Volumes/MARK_DATA/dev/2026-cop-physical-ai
# 대시보드: 시안 수정 후 재베이크→빌드 (서버는 template chokidar 자동반영)
.venv/bin/python3 dashboard/bake_embeds.py && .venv/bin/python3 dashboard/build.py --no-json
# 서버 반영 확인
curl -s localhost:4001/projects/cop-physical-ai/ | grep -c "function initHero3D"
# 헤드리스 렌더 검증 (브라우저 페인=정적스냅샷·JS미실행이라 못 씀; 실 Chrome 헤드리스만 됨)
#   특정 라우트: dashboard.html 사본 </body> 앞에 <script>load→setTimeout(()=>setRoute("playground"),900)</script> 주입 후 렌더
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CHROME" --headless=new --disable-gpu --enable-unsafe-swiftshader --use-gl=angle --use-angle=swiftshader \
  --hide-scrollbars --force-prefers-reduced-motion --window-size=1440,760 --virtual-time-budget=40000 \
  --screenshot=/tmp/chk.png "file://.../dashboard.html"   # → Read /tmp/chk.png
# ↑ 3D는 reduced-motion서 정지프레임(LED-on). interactive/auto-loop은 무한RAF라 reduced-motion 필수(안그럼 virtual-time 행).
# DR 재학습 진행
cat logs/dr_retrain.status ; tail -5 logs/dr_retrain.log
```

---

## 8. 주의 / 함정 (전부)
- **서버=template 서빙**(§1). arm3d/C 수정 시 bake_embeds 재실행 필수. 사용자 강력새로고침.
- **브라우저 페인 wedge/정적스냅샷** — JS 실행 안 됨. 3D/인터랙션 검증은 실 Chrome 헤드리스(위)만.
- **reduced-motion**: 사용자 OS 켜져 있었음(플레이그라운드 멈춤의 원인이었음). D idle은 게이트 제거했음. 3D는 reduced-motion서 정지프레임.
- **Playground 마우스조종 = 스크럽**(팔끝 커서추종 아님). 진짜 3D IK 원하면 별도 큰 작업(브라우저 CCD IK).
- **DR 측정 산출물이 nominal summary 덮어씀**(§5).
- **vault 백업 scratchpad 소멸**(§3).
- **환경 불변 원칙**(사용자 강지시): S1 버튼/스프링/존 실기 기준 불변. DR도 조명/마찰/카메라만·복원.
- **PARA read-only 예외**: 9월 보고서 등 vault 편집은 사용자 "니가 바꿔도됨" 명시 지시로 수행함(원칙상 read-only).

---

## 9. 남은 일 (우선순위)
1. **DR 측정**(§5) — 학습 완료(오늘밤) 후 즉시. 0.45 개선폭 확인 → 승격 판단.
2. **Playground 진짜 커서추종**(3D IK) — 사용자 확인 대기(스크럽으로 충분한지).
3. 대시보드 미세폴리시(스토리 팔 진짜3D 여부는 사용자 "생긴것만"으로 일단 종결).
4. omen 핸드오프(합성셋+0.6.1 로드 스모크), epoch_0029_dr 백업.

**한 줄**: 대시보드 홈을 B(미션컨트롤)로 실적용 완료(Overview 한화면·Story 스크롤유지·Playground 3D실기팔 마우스조종) + RS232 "케이블 분리" 전면정합(repo+vault 22+파일) + ② DR 재학습 가동중(epoch8/30, 오늘밤 완주→측정). 서버=template.html 직접서빙이 핵심(bake_embeds 필수).
