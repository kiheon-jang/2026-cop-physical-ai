# check_act_train.sh — ACT 학습 진행률 표준 status 출력

**날짜**: 2026-06-14 (일)
**Phase**: 1 - W3 사전 준비 D4 (정규 W3: 6/15~6/21)
**상위 항목**: 6/13 research-log "다음 단계" — wrapper 의 짝으로 "다음 날 크론 진행률 체크"
운영 가이드 점검 + 형식 확정.

## 무엇을 했나

`scripts/check_act_train.sh` 신규 작성. PHASE_ROADMAP W3 운영 가이드 (line 124~130)
"매일 크론이 `logs/act_train.log` 마지막 줄 확인 → research-log에 진행률 기록" 항목의
출력 형식을 결정론적으로 고정.

### 책임

1. **pid 살아있음 검증** — `logs/act_train.pid` 읽고 `kill -0 ${PID}` 로 검사.
   `pid=N alive=yes|no|none` 로 단일 라인 출력.
2. **체크포인트 진행률** — `checkpoints/act/epoch_*/` 디렉터리 mtime 최신 + 개수.
   `train_act.py::_save_checkpoint` 가 HF `save_pretrained` 디렉터리 포맷으로 저장하므로
   `epoch_*.pt` 파일 glob 아닌 `-d` 디렉터리 glob 사용 (start_act_train.sh 2회차 패치와
   동일 패턴).
3. **로그 갱신 신선도** — `stat -f '%m' logs/act_train.log` 로 mtime epoch 추출 →
   `log_age_sec` 산출. 24h 이상 미갱신 시 exit 3 (stall 의심).
4. **표준 tail 블록** — `--- last 10 lines ---` 헤더 + `tail -n 10` + `--- end ---` 푸터.
   nightly 에이전트가 이 블록을 그대로 잘라서 research-log "ACT 학습 진행률" 섹션에
   append 하면 형식 통일 보장.
5. **exit code 의미론**:
   - `0` 정상 (pid 살아있음 + 로그 24h 내 갱신)
   - `1` 학습 미시작 (pid 파일 없음)
   - `2` 이상 종료 (pid 파일 있는데 프로세스 죽음)
   - `3` stall 의심 (pid 살아있어도 로그 24h 미갱신)

### 사용 예 (6/16 일 이후 매일 23:00)

```bash
scripts/check_act_train.sh
# 또는 임계값 조정:
TAIL_N=20 STALL_SEC=43200 scripts/check_act_train.sh
```

### 표준 출력 샘플 (W3 D2 가정)

```
pid=12345 alive=yes
ckpt_latest=epoch_0007 ckpt_count=8
log_size=204800 log_mtime=2026-06-16T22:45:12Z log_age_sec=900
--- last 10 lines ---
epoch 7 step 1200 loss=0.0421 lr=1.0e-4 elapsed=2h41m
...
--- end ---
```

## 어떻게 검증했나

- 본 세션 sandbox 가 `bash -n` / `chmod +x` / `.venv/bin/python3` 실행 차단 (6/7 이후
  14일 연속). 정적 검증만:
  - shebang `#!/usr/bin/env bash` + `set -uo pipefail` (errexit 제외 — exit code 1/2/3 을
    의도적으로 반환).
  - `stat -f '%z'`, `stat -f '%m'`, `date -r` 모두 macOS BSD stat 형식 (Mac mini M5 호환).
  - `${TAIL_N:-10}`, `${STALL_SEC:-86400}` 기본값 패턴으로 환경변수 override.
  - pid 파일 없을 때 / 로그 파일 없을 때 / checkpoint 디렉터리 없을 때 모두 분기 가드.
- start_act_train.sh 와 정합성: 동일한 `${ROOT}` / `logs/` / `checkpoints/act/` 경로 사용.
- 어제(6/13) 자가치유 기록의 ".venv/bin/python3 부재" 주장은 오기록 — 실제로 `.venv/bin/`
  에 `python`, `python3`, `python3.14`, `mjpython` 모두 존재 (`ls .venv/bin/ | grep python`
  확인). mjpython 단일이라는 표현은 사실이 아님. 본 회차 정정.

## 다음 단계와의 연결

- **6/15 (월) Phase 1 W3 D1**: `scripts/train_act.py --smoke` → `start_act_train.sh
  --epochs 100` 백그라운드 실행 → PHASE_ROADMAP W3 첫 두 항목 `[v]` 체크.
- **6/16 (화) ~ W3 종료**: 매일 23:00 nightly 가 `check_act_train.sh` 호출, 출력을
  research-log "ACT 학습 진행률" 섹션에 통째로 append. exit code 2/3 발생 시
  external-dependencies.md 에 incident 항목 추가.
