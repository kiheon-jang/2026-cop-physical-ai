# start_act_train.sh — ACT 학습 시작 wrapper

**날짜**: 2026-06-13 (토)
**Phase**: 1 - W3 사전 준비 D3 (정규 W3: 6/15~6/21)
**상위 항목**: 6/12 research-log "다음 단계" — wrapper 신규.

## 무엇을 했나

`scripts/start_act_train.sh` 신규 작성. 6/15 (Phase 1 W3 D1) 부터
`scripts/train_act.py --epochs 100` 본 학습을 nohup 백그라운드로 띄우기 위한 진입점.

### 책임

1. **venv 절대경로 강제** — `/Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv/bin/python3`
   를 직접 호출. PATH 의존성 제거 (크론 환경에서도 동일하게 동작).
2. **MPS fallback 환경변수** — `PYTORCH_ENABLE_MPS_FALLBACK=1` 명시. M5 MPS 가
   ACT 일부 op 미지원 시 CPU 폴백 (NotImplementedError 회피).
3. **자동 resume** — `checkpoints/act/epoch_*.pt` 중 mtime 최신을 골라
   `--resume-from <path>` 자동 부착. 체크포인트 없으면 cold start.
4. **pid 관리** — `logs/act_train.pid` 기록. 기존 pid 가 살아 있으면 즉시 exit 2
   (이중 실행 방지). 죽은 pid 면 파일만 정리하고 새로 시작.
5. **로그 append** — `logs/act_train.log` 에 stdout/stderr 추가 기록. 다음 날 크론이
   이 파일 tail 로 진행률 확인.

### 사용 예

```bash
scripts/start_act_train.sh                 # config.num_epochs (200)
scripts/start_act_train.sh --epochs 100    # PHASE_ROADMAP 권장
scripts/start_act_train.sh --smoke         # 1 epoch sanity check
tail -f logs/act_train.log
kill "$(cat logs/act_train.pid)"           # 중단
```

## 어떻게 검증했나

- 본 세션 sandbox 가 `bash -n` / `chmod +x` 차단 (6/7 이후 13일 연속, 자가치유 항목 참조).
  → 정적 검증만:
  - shebang `#!/usr/bin/env bash` + `set -euo pipefail` 표준.
  - PID 파일 race: `kill -0 ${OLD_PID}` 로 살아있음 여부 확인 후 분기.
  - resume 탐색: `ls -t epoch_*.pt | head -n 1`. 없을 때 `|| true` 로 set -e 회피.
  - 사용자 추가 인자(`$@`) 가 `--resume-from` 뒤로 와서 명시 `--resume-from` 지정 시
    덮어쓰기 가능 (argparse 의 마지막 값 우선 규칙).
- 6/15 W3 D1 실행 시 `--smoke` 1 회 → `--epochs 100` 백그라운드 띄우는 절차로 통합.

## 다음 단계와의 연결

- **6/14 (일)**: 본 wrapper 와 짝이 될 "다음 날 크론 진행률 체크" 로직 점검. 매일
  Hermes 가 `logs/act_train.log` 마지막 줄 + `logs/act_train.pid` 살아있음 여부를
  research-log 에 기록하도록 PHASE_ROADMAP W3 운영 가이드 (line 124~130) 와 일치하는지
  확인.
- **6/15 (월) Phase 1 W3 D1**: `scripts/train_act.py --smoke` 통과 → 본 wrapper 로
  `--epochs 100` 백그라운드 실행 → PHASE_ROADMAP W3 첫 두 항목 `[v]` 체크.

---

## 2회차 — 23:00 nightly 정합성 패치

본 회차 진입 시점에 01:02 회차가 작성한 wrapper 가 워킹트리에 존재(untracked, mtime
2026-06-13 01:02). 정독 후 **자동 resume glob 미스매치** 발견 — 1회차 헤더/검증 섹션이
"`epoch_*.pt` 파일" 가정으로 작성되었으나 `scripts/train_act.py::_save_checkpoint`
(line 250~265) 는 `Path(config.checkpoint_dir) / f"epoch_{epoch:04d}"` **디렉터리** 에
`ACTPolicy.save_pretrained` (HF 포맷) 저장. `ls -t epoch_*.pt` glob 은 항상 빈 결과 →
auto-resume 영구 무효 상태.

### 본 회차 변경 (Edit 도구만 사용)

1. **resume 탐색 패턴 교정**
   - `ls -t "${CKPT_DIR}"/epoch_*.pt` → `ls -dt "${CKPT_DIR}"/epoch_*/` (디렉터리만
     mtime 최신순). 후행 슬래시 제거 + `-d` 존재 검증 추가.
2. **사용자 인자 충돌 가드 추가**
   - 사용자가 `--resume-from <path>` 또는 wrapper 전용 `--no-resume` 을 직접 넘긴 경우
     자동 탐색 분기 자체 생략 (`SKIP_AUTO_RESUME=1`).
   - 기존 1회차 코드는 `RESUME_ARG` + `$@` 를 그대로 이어붙여 argparse 마지막 값 우선에
     의존했으나, 명시성 향상 + smoke 경로에서 인자 한 줄짜리 진단 메시지 노출 목적으로
     분리.
3. **`--no-resume` wrapper 전용 플래그 신규**
   - 의도적 cold-start 강제용. `FILTERED_ARGS` 로 분리해 `train_act.py` 에는 전달하지
     않는다 (argparse 미정의 인자로 거부되는 것 방지).
4. **set -u 빈 배열 expansion 안전성**
   - `${FILTERED_ARGS[@]+"${FILTERED_ARGS[@]}"}` 패턴으로 빈 배열 unbound 회피.
5. **헤더 주석 갱신** — "`epoch_*.pt`" → "`epoch_*/` 디렉터리 (HF save_pretrained)".

### 본 회차 검증

- 정적: Edit 후 변경 라인 reread 로 적용 확인.
- 런타임: `bash -n scripts/start_act_train.sh` / `chmod +x scripts/start_act_train.sh`
  본 세션 sandbox 차단 (13일 연속, 6/7~6/13). 실행 검증은 6/15 W3 D1 `--smoke` 시 일괄
  수행.
- 정합성 grep:
  - `scripts/train_act.py:390` (`--resume-from` argparse), `:451` (`build_model` 전달),
    `:180,234` (`from_pretrained` 디렉터리 로드).
  - `scripts/train_act.py:258-261` (`epoch_{epoch:04d}` 디렉터리 + `save_pretrained`).

### 본 회차 자가치유

- [자가치유] `chmod +x scripts/start_act_train.sh` → "This command requires approval" 거절.
  실행 권한 미부여 상태로 commit 진입. 6/15 W3 D1 사용자 수동 `chmod +x` 1회 필요 또는
  `bash scripts/start_act_train.sh ...` 명시 실행.
- [자가치유] `bash -n scripts/start_act_train.sh` 구문 검사 sandbox 차단. 정적 reread 만
  수행.

