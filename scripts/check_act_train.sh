#!/usr/bin/env bash
# ACT 학습 진행률 체크 (start_act_train.sh 의 짝).
#
# 매일 23:00 nightly 크론이 호출 → 표준 status 블록을 stdout 으로 출력.
# 크론 에이전트는 출력을 그대로 research-log 의
# "## ACT 학습 진행률" 섹션에 append.
#
# 출력 형식 (PHASE_ROADMAP line 124~130 운영 가이드 일치):
#   pid=<N> alive=<yes|no|none>
#   ckpt_latest=<dir-or-none> ckpt_count=<N>
#   log_size=<bytes> log_mtime=<iso8601>
#   --- last 10 lines ---
#   <tail>
#   --- end ---
#
# exit code:
#   0  pid 살아있음 + 로그 갱신 정상
#   1  pid 파일 없음 (학습 미시작)
#   2  pid 파일 있는데 프로세스 죽음 (이상 종료)
#   3  로그 24h 이상 미갱신 (stall 의심)

set -uo pipefail

ROOT="/Volumes/MARK_DATA/dev/2026-cop-physical-ai"
LOG_FILE="${ROOT}/logs/act_train.log"
PID_FILE="${ROOT}/logs/act_train.pid"
CKPT_DIR="${ROOT}/checkpoints/act"
TAIL_N="${TAIL_N:-10}"
STALL_SEC="${STALL_SEC:-86400}"

# pid 상태.
PID="none"
ALIVE="none"
if [[ -f "${PID_FILE}" ]]; then
  PID="$(cat "${PID_FILE}" 2>/dev/null || echo none)"
  if [[ -n "${PID}" && "${PID}" != "none" ]] && kill -0 "${PID}" 2>/dev/null; then
    ALIVE="yes"
  else
    ALIVE="no"
  fi
fi

# checkpoint 상태 (train_act.py 는 epoch_NNNN/ 디렉터리에 HF save_pretrained).
CKPT_LATEST="none"
CKPT_COUNT=0
if [[ -d "${CKPT_DIR}" ]]; then
  LATEST="$(ls -dt "${CKPT_DIR}"/epoch_*/ 2>/dev/null | head -n 1 || true)"
  if [[ -n "${LATEST}" ]]; then
    CKPT_LATEST="$(basename "${LATEST%/}")"
  fi
  CKPT_COUNT="$(ls -d "${CKPT_DIR}"/epoch_*/ 2>/dev/null | wc -l | tr -d ' ')"
fi

# log 상태.
LOG_SIZE=0
LOG_MTIME="none"
LOG_AGE_SEC=-1
if [[ -f "${LOG_FILE}" ]]; then
  LOG_SIZE="$(stat -f '%z' "${LOG_FILE}" 2>/dev/null || echo 0)"
  LOG_MTIME_EPOCH="$(stat -f '%m' "${LOG_FILE}" 2>/dev/null || echo 0)"
  LOG_MTIME="$(date -r "${LOG_MTIME_EPOCH}" -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo none)"
  NOW_EPOCH="$(date -u +%s)"
  LOG_AGE_SEC=$(( NOW_EPOCH - LOG_MTIME_EPOCH ))
fi

echo "pid=${PID} alive=${ALIVE}"
echo "ckpt_latest=${CKPT_LATEST} ckpt_count=${CKPT_COUNT}"
echo "log_size=${LOG_SIZE} log_mtime=${LOG_MTIME} log_age_sec=${LOG_AGE_SEC}"
echo "--- last ${TAIL_N} lines ---"
if [[ -f "${LOG_FILE}" ]]; then
  tail -n "${TAIL_N}" "${LOG_FILE}" 2>/dev/null || true
else
  echo "(log 없음)"
fi
echo "--- end ---"

# exit code 분기.
if [[ "${PID}" == "none" ]]; then
  exit 1
fi
if [[ "${ALIVE}" == "no" ]]; then
  exit 2
fi
if [[ "${LOG_AGE_SEC}" -ge "${STALL_SEC}" ]]; then
  exit 3
fi
exit 0
