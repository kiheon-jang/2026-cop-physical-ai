#!/usr/bin/env bash
# CoP Physical AI — 시뮬 데이터 자동수집 nohup 래퍼 (closed-loop expert).
#
# cop_pipeline_advance.sh(야간 파이프라인 드라이버)가 호출한다.
# start_act_train.sh 와 동일 패턴: .venv 절대경로 + nohup 백그라운드 + pid/log + 중복방지.
#
# 데이터 경로: data/episodes_cl  (cl = closed-loop. 기존 open-loop data/episodes 보존).
#   → train_act.py 는 COP_DATASET_ROOT=data/episodes_cl 로 이 데이터를 읽는다.
#
# 네이밍: 다른 프로젝트 잡과 안 헷갈리게 모두 cop_ 접두.
#   pid : logs/cop_data_collect.pid   log : logs/cop_data_collect.log
#
# 사용:
#   scripts/cop_start_data_collect.sh [EPISODES]   # 기본 50
set -euo pipefail

ROOT="/Volumes/MARK_DATA/dev/2026-cop-physical-ai"
PY="${ROOT}/.venv/bin/python3"
COLLECTOR="${ROOT}/samples/training/sim_data_collector.py"
# 드라이버가 COP_DATA_DIR 로 타겟 데이터셋을 넘긴다 (기본: 운영 episodes_cl)
DATA_DIR="${COP_DATA_DIR:-${ROOT}/data/episodes_cl}"
LOG_DIR="${ROOT}/logs"
PID_FILE="${LOG_DIR}/cop_data_collect.pid"
LOG_FILE="${LOG_DIR}/cop_data_collect.log"
EPISODES="${1:-50}"

mkdir -p "${LOG_DIR}"

if [[ ! -x "${PY}" ]]; then
  echo "[cop_data_collect] .venv python 없음: ${PY}" >&2
  exit 1
fi

# 중복 실행 방지
if [[ -f "${PID_FILE}" ]]; then
  OLD_PID="$(cat "${PID_FILE}" 2>/dev/null || true)"
  if [[ -n "${OLD_PID}" ]] && kill -0 "${OLD_PID}" 2>/dev/null; then
    echo "[cop_data_collect] 이미 실행 중 (pid=${OLD_PID}). 중복 실행 방지." >&2
    exit 2
  fi
  rm -f "${PID_FILE}"
fi

cd "${ROOT}"
export PYTORCH_ENABLE_MPS_FALLBACK=1

# closed-loop expert로 성공 시연만 수집 (sim_data_collector.py 가 lift>=40mm 필터).
nohup "${PY}" "${COLLECTOR}" --root "${DATA_DIR}" --episodes "${EPISODES}" \
  > "${LOG_FILE}" 2>&1 &
echo $! > "${PID_FILE}"
echo "[cop_data_collect] 시작 pid=$(cat "${PID_FILE}") → ${DATA_DIR} (${EPISODES}ep) log=${LOG_FILE}"
