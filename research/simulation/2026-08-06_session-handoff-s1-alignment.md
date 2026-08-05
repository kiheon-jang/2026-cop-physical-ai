# 세션 인수인계 — 2026-08-05 15:30 ~ 08-06 02:30 (S1 정렬 + 사이트 전면 정비)

> 다음 세션이 이어받을 수 있도록 이 세션의 **진행·리서치·확인·정리 전부**를 기록한다.
> 관련 커밋: `6c40b1c` ~ `772774f` (CoP 14건) + hermes-mark `4925887`, `de161ca`.

---

## 0. 지금 돌아가고 있는 것 (재시작 시 가장 먼저 확인)

| 항목 | 상태 | 확인 방법 |
|------|------|-----------|
| **S1 ACT 학습** | in-flight — pid 65874, 30 epochs, 8/5 23:02 시작, 완주 ~8/6 10:20 예상. 마지막 확인 epoch 6 loss 0.133 | `tail logs/s1_train_30ep.log` / `grep epoch_done logs/s1_train_30ep.log \| tail -1` |
| **04:04 killer 확증 실험** | 이 학습이 04:04 를 일부러 관통한다. **살아 있으면 가설 확증**(원인 = gateway 그룹 한정), 죽었으면 가설 기각 + epoch 9/19/29 ckpt 로 재개 | 아침에 `ps -p 65874` + 로그 연속성 |
| 체크포인트 | `checkpoints/act_s1_sim/epoch_00NN` (10 epoch 마다) | `ls checkpoints/act_s1_sim/` |
| 야간 크론 | 손 안 댐 — 여전히 1단계 회귀+무결성 감사 (S1 전환은 W3 측정기 후) | `agent/cron-jobs.md` |

---

## 1. 이 세션에서 규명한 것 (리서치·확인)

### 1-1. 사이트가 빈 화면이던 원인 2건 (수정 완료)
1. **`rateColor` ReferenceError** — 함수가 스크립트 3 블록에 있는데 스크립트 1 init 이 호출.
   `<script>` 블록 간 hoisting 없음 → `drawAllCharts()`·`IS_LIVE` 부트스트랩까지 사망 →
   라이브 페이지 전체 빈칸. 수정: 함수를 사용 지점 앞으로 + IS_LIVE 부트스트랩을 렌더보다 먼저.
2. **fastify-compress 0바이트** (hermes-mark) — async 핸들러가 `reply.send(tpl)` 후 undefined
   반환 → Fastify 가 2차 send 로 압축 스트림을 덮어씀 → `Accept-Encoding` 보내는 모든 브라우저에
   Content-Length: 0. curl(무압축)만 정상이라 은폐돼 있었다. 수정: `return reply...send(tpl)`.

### 1-2. 진척률 38% 의 절반은 측정 버그 (수정 완료)
- 로드맵 파서가 `### W1` 헤딩만 인식 — Phase 2~4 의 `- W1 (…):` 대시 형식 전부 0/0 처리.
- 7/2~7/22 성과가 체크박스로 승격 안 돼 있었음 → 승격. 38% → 53% (→ W1·W2 완료로 현재 63%+).
- 지연 표시는 "가장 앞선 진행 phase" 기준으로 재정의 (`advanced_phase_*`).

### 1-3. 실기 트랙 리서치 (deois/soarm_lerobot — 61커밋 전수 분석)
- **머신 omen**: Ubuntu 22.04, RTX 2080 Ti 11GB, lerobot **0.6.1** (Mac 은 0.5.1 — API 차이 주의).
- **팔 2대 모두 omen 연결**, 텔레오퍼 ~60Hz 검증. 카메라 top(C920 광각)/closeup(Realtek 근접) 640×480@30.
- 작업 **S1 = PCB 리셋버튼 누르기**, **P1 = 녹색 LED 판정**(OpenCV 규칙, MVP 합격선 80%).
- 진행: 데이터 10ep(목표 80), ACT 20k steps 정책 2개 — `pcb_reset`(유효) / `act_s1`(카메라 라벨
  뒤바뀐 데이터로 학습 — 사용 금지 문서화됨). **롤아웃 성공률 미측정, LED ROI 미캘리브(placeholder)**.
- 실기의 결핍 2 = 데이터 부족 + 성공판정 부재 → **시뮬이 메울 지점** (Phase 3 재정의 근거).
- **Orin Nano SSH 블로커 전제 무효** — 실기 경로는 omen 협업. Orin 은 10월 시연 항목으로 보류 처리.
- 로컬 미러: `/Volumes/MARK_DATA/dev/soarm_lerobot` (LFS 스킵). `build.py::build_real_track()` 이
  rebuild 마다 자동 `git pull` → 사이트 "실기 트랙" 메뉴 갱신.

### 1-4. **04:04 killer 종결** (7월 12-run 연쇄 사망 미제 — 원인 확정)
- 범인 = **`ai.hermes.autoupdate`** (launchd StartCalendarInterval **04:00**).
- 메커니즘: 업데이트 시도(요즘 매일 실패→롤백) → gateway 를 `launchctl kickstart -k` 재시작 →
  **gateway 프로세스 그룹 전체 SIGKILL**. 야간 크론(gateway 자식)이 nohup 으로 띄운 학습이 같은
  그룹이라 동반 사살 (nohup 은 SIGHUP 만 무시).
- 증거: 백업 zip `pre-update-*-0400xx`, gateway.log 04:03:52 재시작(8/5), 12-run 사망 시각 일치.
- **수정**: `scripts/start_act_train.sh` 가 학습을 `start_new_session`(새 세션 = 새 프로세스 그룹)
  으로 분리. 스모크로 PGID 분리 확인. 상세: `agent/external-dependencies.md` 04:04 항목.

---

## 2. Phase 3 진행 (W1·W2 하루에 완료 — 1주 선행)

### W1 — 실기 트윈 씬 정합 (4/4, 자가검증 PASS)
- `sim/assets/pcb_reset_scene.xml` — 실기 씬 이식 + 정합. **메인 레포에 배치**(SO-ARM100 중첩
  레포 유실 위험 회피). assets 심링크로 mesh 해결.
- 버튼 눌림 메커니즘: 슬라이드 조인트(z, 3mm) + 스프링(150) + 임계 -1.5mm.
  **환경 불변 원칙(사용자 지시)**: 버튼 치수·스프링·존 = 실기 원본 그대로. 돌출 상향 시도는 철회.
  유일 수정 = 버튼↔보드 contact exclude (원본은 버튼이 보드에 눌러붙어 물리적으로 안 눌리는
  버그 — 실물은 보드 구멍 관통 구조).
- top/closeup 카메라 2대(실기 배치 근사, 육안 검증), `HOME_QPOS` 홈 자세(top 뷰 가림 해소).
- 15×15cm 존 무작위화 (x 0.15~0.30 × y ±0.075, yaw ±10°).
- 모듈: `samples/training/sim_pcb_reset.py` (`PcbResetTwin`, `__main__` 자가검증 4/4).

### W2 — expert + 100ep 합성 (완료, omen 스모크만 잔여)
- **expert 20-seed 95%** (`samples/training/sim_pcb_reset_collector.py`):
  - TCP(패드 갭 중점) 겨냥은 0/5 — **jaw 끝 접촉점**(`PRESS_LOCAL = [0.0114,-0.0001,-0.1044]`,
    빈 보드 상면 접촉 실측 캘리브)으로 겨냥해야 한다.
  - pan 정렬 → 버튼 위 60mm 경유 → 단계 하강(+30/+10/+3/-2.5mm, 매 단계 IK 재계산) →
    LED 확인 → 리트랙+재관측 재시도(최대 3).
  - 남는 실패 5% = 존 구석의 **기하 도달불가** 배치(IK 자세 강제 관통검사로 확정 — press 자세가
    팔 링크의 보드 2.5mm 관통 요구. 같은 SO-101 인 실기도 동일).
- **100ep/7,231frame 합성** (`data/episodes_s1`, 58MB, yield 93%, seed 20260805).
  LeRobotDataset 전수 재로드 검증: **v3.0**, top+closeup 640×480, state/action 6,
  task `"press the reset button"` — 실기 계약과 동일. Mac lerobot 0.5.1 도 v3.0 emit 확인.
- PCB 배치 사이드카 `meta/pcb_traj.json` (100ep 소급 = 수집 로그 성공 라인 순서; 이후 수집분은
  수집기가 직접 기록).
- **잔여**: omen lerobot 0.6.1 로드 스모크 (실기 담당자 협업 — W4 핸드오프와 병합 가능).

### W3 착수 (학습 in-flight)
- `scripts/train_act.py` 에 env 오버라이드 2개 추가: `COP_CAMERA_KEYS`(top,closeup),
  `COP_DATASET_REPO_ID`(local/pcb_reset_sim). 스모크 통과.
- 학습 실행 커맨드 (재현용):
  ```
  COP_DATASET_ROOT=$PWD/data/episodes_s1 COP_DATASET_REPO_ID=local/pcb_reset_sim \
  COP_CAMERA_KEYS=top,closeup COP_CKPT_DIR=$PWD/checkpoints/act_s1_sim \
  nohup .venv/bin/python3 scripts/train_act.py --epochs 30 > logs/s1_train_30ep.log 2>&1 &
  ```
- epoch 당 ~23분 (2카메라 디코드 — 1카메라 때의 2배).

---

## 3. 사이트 전면 정비 (혼돈 제거)

### 구조
- **실기 트랙 메뉴 신설** — 미러 자동 pull, KPI/데이터셋/정책 테이블, 커밋·문서는 접힘.
- **시각자료 재구성**: 지금 진행(S1 시범 100회 — "AI 가 이걸 보고 배운다") → 2단계 학습
  현황(라이브) → 1단계 시험 영상 히스토리 → **아카이브(접힘)**.
- **3D 리플레이**: S1 에피소드 재생(PCB+버튼+LED 오버레이, 배치 사이드카), 기본 선택 = S1,
  옛 측정은 [아카이브] 프리픽스, policy_history 중복 dedupe 9→4.
- **홈**: 스토리 스트립(3문장 + 3단계 카드), 일정 대비 진척 바(시간 63% vs 진척), 스펙트럼 제거(중복).
- **성과 지표**: 성적표 요약 2장(1단계 졸업 ✓ / 2단계 학습 중) + 전문 데이터 접힘.
- S1 영상 서빙: hermes-mark `/static/cop/` 화이트리스트에 `data/episodes_s1/videos/` (mp4 만).

### 정확성 수정 (숫자가 틀려 보이던 것)
- **공정추정 82.5% → 1.0**: 계산이 구모델 seed 요약에 고정 → 현행 모델(latest ckpt_dir) 기준.
- 학습 메트릭이 6개 run 혼합 1,015 epoch 을 한 run 처럼 표시 → run 경계(ckpt_dir 변화)로 분리.
- `current_phase_*` = 가장 앞선 진행 phase (explainer "지금 = 6월" 오표시 근원 제거).

### 용어 사전 (canon — 전 파일 통일 완료)
- 1단계 = **물건 집어 옮기기 (Pick & Place)** · 완료(4-seed 1.0)
- 2단계 = **PCB 리셋 버튼 누르기 (S1)** · 진행 중 (시뮬+실기)
- 3단계 = **RS232 케이블 연결** (점검 단말기 HHT 를 PCB 포트에 꽂기) · 예정
  ("결선"/"통신 학습"/"케이블 꽂기" 표기 전부 제거 — 렌더 DOM 전 라우트 스캔 잔존 0)
- 모든 메뉴 첫 줄 = "**여기서 보는 것 —** ..." 포맷.

---

## 4. 다음 세션 할 일 (우선순위 순)

1. **04:04 확증 판정** — 학습 생존 확인(§0). 생존 시 external-dependencies 항목 종결 표기.
2. **W3 측정기** — S1 rollout 측정 스크립트 (`render_act_rollout.py` 패턴):
   LED latch 자동 채점 · 4-seed 프로토콜 · **rollout 영상 emit**(사용자 요청 — 시각자료
   "학습 진척"에 S1 시험 영상 추가) · `rollout_summary_s1*.json` + history/traj (3D 리플레이
   정책 그룹 자동 연동 — sim3dModelLabel 에 act_s1_sim 이미 등록).
3. **크론 드라이버 S1 전환** — `logs/cop_dataset_target` → episodes_s1 + 드라이버 측정 스테이지가
   S1 측정기를 쓰도록. (`~/.hermes/scripts/cop_*` 쪽도 확인.)
4. **omen 핸드오프** — 합성 데이터셋 전달 + 0.6.1 로드 스모크 (실기 담당자 협업 채널 필요).
5. **디자인 전면 개편** — 사용자 예고. 콘텐츠·구조·용어 정리 완료 상태라 착수 가능.
6. **Obsidian 7·8월 보고서 본문 현행화** — 사용자 명의 문서라 미수정. 사용자 결정 대기
   (7월: "50ep 수집 예정" 초안 그대로 / 8월: "PCB 조정 진입 예정" — 실제는 S1).
7. **SO-ARM100 자산 백업 결정** — `scene_grasp_floor.xml` 이 중첩 레포에 untracked (유실 위험).
   포크(kiheon-jang/SO-ARM100) vs 메인 레포 복사. 사용자 결정 대기.

## 5. 알려진 제약 / 주의
- **환경 불변 원칙**: S1 씬의 버튼 치수·스프링·존 은 실기(엘리베이터 제어반) 기준 — 성공률을
  위해 바꾸지 말 것 (사용자 강지시).
- 카메라 이름 계약 top/closeup 고정 (실기 camswap 사고 전례).
- Mac lerobot 0.5.1 ↔ omen 0.6.1 — CLI/API 차이. 데이터 포맷은 양쪽 v3.0.
- hermes-mark 서버는 launchd `com.hermesmark.server` (KeepAlive) — 재시작은 `kickstart -k`.
- `data/episodes_s1` 은 gitignore (대용량) — 사이드카 포함 재생성 가능(수집기+seed).
