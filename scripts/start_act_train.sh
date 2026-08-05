#!/usr/bin/env bash
# ACT 학습 시작 wrapper (Phase 1 W3 D1, 6/15 이후 사용).
#
# 역할:
#   1) .venv 절대경로 python 강제
#   2) PYTORCH_ENABLE_MPS_FALLBACK=1 명시 (M5 MPS 미지원 op → CPU fallback)
#   3) checkpoints/act/epoch_*/ 디렉터리 중 mtime 최신 → --resume-from 자동 부착
#      (train_act.py 는 HF save_pretrained 형식의 *디렉터리* 로 저장)
#   4) nohup 백그라운드 실행 + logs/act_train.pid 기록 + logs/act_train.log tee
#   5) 이미 실행 중인 pid 발견 시 즉시 중단 (이중 실행 방지)
#
# 사용:
#   scripts/start_act_train.sh                 # config 기본 epoch
#   scripts/start_act_train.sh --epochs 100    # 100 epoch
#   scripts/start_act_train.sh --smoke         # 1 epoch / 2 step smoke
#
# 종료 후:
#   tail -f logs/act_train.log
#   kill "$(cat logs/act_train.pid)"   # 중단

set -euo pipefail

ROOT="/Volumes/MARK_DATA/dev/2026-cop-physical-ai"
PY="${ROOT}/.venv/bin/python3"
TRAIN_SCRIPT="${ROOT}/scripts/train_act.py"
# 드라이버가 COP_CKPT_DIR 로 데이터셋별 체크포인트 디렉터리를 넘긴다 (train_act.py 도 동일 env 사용)
CKPT_DIR="${COP_CKPT_DIR:-${ROOT}/checkpoints/act}"
LOG_DIR="${ROOT}/logs"
PID_FILE="${LOG_DIR}/act_train.pid"
LOG_FILE="${LOG_DIR}/act_train.log"

mkdir -p "${LOG_DIR}" "${CKPT_DIR}"

if [[ ! -x "${PY}" ]]; then
  echo "[start_act_train] .venv python 없음: ${PY}" >&2
  exit 1
fi

if [[ -f "${PID_FILE}" ]]; then
  OLD_PID="$(cat "${PID_FILE}")"
  if [[ -n "${OLD_PID}" ]] && kill -0 "${OLD_PID}" 2>/dev/null; then
    echo "[start_act_train] 이미 실행 중 (pid=${OLD_PID}). 중단 후 재실행 필요." >&2
    exit 2
  fi
  rm -f "${PID_FILE}"
fi

# 최신 체크포인트 자동 탐색.
# train_act.py::_save_checkpoint 는 epoch_NNNN/ 디렉터리(HF save_pretrained) 로 저장.
# 사용자가 --resume-from 을 명시했거나 --no-resume(wrapper 전용 플래그)을 넘기면 자동 탐색 생략.
RESUME_ARG=()
SKIP_AUTO_RESUME=0
for arg in "$@"; do
  case "${arg}" in
    --resume-from|--resume-from=*|--no-resume) SKIP_AUTO_RESUME=1 ;;
  esac
done

if [[ "${SKIP_AUTO_RESUME}" -eq 0 ]]; then
  LATEST_CKPT="$(ls -dt "${CKPT_DIR}"/epoch_*/ 2>/dev/null | head -n 1 || true)"
  LATEST_CKPT="${LATEST_CKPT%/}"
  if [[ -n "${LATEST_CKPT}" && -d "${LATEST_CKPT}" ]]; then
    RESUME_ARG=(--resume-from "${LATEST_CKPT}")
    echo "[start_act_train] resume: ${LATEST_CKPT}"
  else
    echo "[start_act_train] resume 없음 (cold start)"
  fi
else
  echo "[start_act_train] 사용자 인자에 --resume-from/--no-resume 존재 — 자동 탐색 생략"
fi

# --no-resume 은 wrapper 전용 플래그 → train_act.py 에는 전달하지 않는다.
FILTERED_ARGS=()
for arg in "$@"; do
  [[ "${arg}" == "--no-resume" ]] || FILTERED_ARGS+=("${arg}")
done

export PYTORCH_ENABLE_MPS_FALLBACK=1

cd "${ROOT}"

# setsid(새 세션) 필수 — nohup 만으로는 부족하다.
# 2026-08-05 규명: 12-run 연쇄 이상종료(~04:04 고정)의 원인은 ai.hermes.autoupdate
# (launchd, 매일 04:00)가 업데이트 실패 → 롤백 → gateway 를 kickstart 로 재시작하면서
# gateway 프로세스 그룹 전체에 SIGKILL 을 보내는 것. 이 스크립트가 hermes cron
# (gateway 자식)에서 실행되면 nohup 학습 프로세스도 같은 그룹이라 동반 사살된다
# (nohup 은 SIGHUP 만 무시, SIGKILL 은 못 막음). 새 세션 = 새 프로세스 그룹 → 생존.
# macOS 에는 setsid CLI 가 없어 파이썬 wrapper(start_new_session)를 쓴다.
nohup "${PY}" -c "
import subprocess, sys
p = subprocess.Popen(sys.argv[1:], start_new_session=True)
print(p.pid, flush=True)
" "${PY}" "${TRAIN_SCRIPT}" "${RESUME_ARG[@]+"${RESUME_ARG[@]}"}" "${FILTERED_ARGS[@]+"${FILTERED_ARGS[@]}"}" \
  >> "${LOG_FILE}" 2>&1 &

# wrapper 가 stdout 첫 줄에 실제 학습 pid 를 출력한다 — 잠깐 대기 후 회수.
sleep 2
NEW_PID="$(tail -n 5 "${LOG_FILE}" | grep -E '^[0-9]+$' | tail -n 1 || true)"
if [[ -z "${NEW_PID}" ]]; then
  NEW_PID=$!   # 폴백: wrapper pid (학습 pid 회수 실패 시에도 파이프라인은 계속)
fi
echo "${NEW_PID}" > "${PID_FILE}"
echo "[start_act_train] 시작 pid=${NEW_PID} log=${LOG_FILE} args=$*"
