#!/usr/bin/env bash
# CoP Physical AI — 시뮬 파이프라인 결정론적 드라이버.
#
# 야간 cron(cop-physical-ai-self-heal 스킬)이 매 실행 첫 액션으로 이걸 호출한다.
# LLM 판단 없이 상태만 보고 다음 1단계를 백그라운드로 전진시킨다 → 매일 한 칸씩 진척.
# (self-heal LLM 은 "진짜 에러/stall" 일 때만 보조. 전진은 이 결정론 스크립트가 담당.)
#
# 단계(우선순위 순, 1회 1단계):
#   1) 수집 진행중   → 상태만 보고
#   2) 학습 진행중   → check_act_train.sh 로 진행률 보고
#   3) 데이터 부족   → cop_start_data_collect.sh (closed-loop 수집, nohup)
#   4) 데이터 준비됨 & 이 데이터로 미학습 → start_act_train.sh (ACT 재학습, nohup)
#   5) 학습 완료 & 이 모델 미측정 → render_act_rollout.py (성공률 측정)
#   6) 측정 완료     → 수렴 판정 + 상태 보고
#
# 출력: "CoP 시뮬 파이프라인" 상태블록 → cron 이 research-log + 아침 메일에 그대로 append.
# 네이밍: 모든 산출물 cop_ 접두 (다른 프로젝트 잡과 격리).
set -uo pipefail

ROOT="/Volumes/MARK_DATA/dev/2026-cop-physical-ai"
PY="${ROOT}/.venv/bin/python3"
LOG_DIR="${ROOT}/logs"
DATA_DIR="${ROOT}/data/episodes_cl"
MODEL="${ROOT}/models/act_phase1.pt"

TARGET_EP="${COP_TARGET_EP:-50}"        # 목표 성공 에피소드 수
TARGET_RATE="${COP_TARGET_RATE:-0.90}"  # 목표 rollout 성공률
EPOCHS="${COP_EPOCHS:-100}"

COLLECT_PID="${LOG_DIR}/cop_data_collect.pid"
TRAIN_PID="${LOG_DIR}/act_train.pid"
TRAINED_MARK="${LOG_DIR}/cop_trained_on.marker"     # 학습에 쓴 데이터 서명
MEASURED_MARK="${LOG_DIR}/cop_measured.marker"      # 측정한 모델 서명
ROLLOUT_LOG="${LOG_DIR}/cop_rollout.log"

cd "${ROOT}"
mkdir -p "${LOG_DIR}"

# pid 파일이 가리키는 프로세스가 살아있나
pid_alive() {
  local f="$1"
  [[ -f "$f" ]] || return 1
  local p; p="$(cat "$f" 2>/dev/null || true)"
  [[ -n "$p" ]] && kill -0 "$p" 2>/dev/null
}
# LeRobot 데이터셋의 에피소드 수
data_episodes() {
  [[ -f "${DATA_DIR}/meta/info.json" ]] || { echo 0; return; }
  "${PY}" -c "import json,sys
try: print(json.load(open('${DATA_DIR}/meta/info.json')).get('total_episodes',0))
except Exception: print(0)" 2>/dev/null || echo 0
}
# 파일 mtime (서명용)
sig() { stat -f '%m' "$1" 2>/dev/null || echo 0; }

echo "════════ 🤖 CoP Physical AI 시뮬 파이프라인 ($(date '+%Y-%m-%d %H:%M')) ════════"

# ── 1. 수집 진행중 ──
if pid_alive "${COLLECT_PID}"; then
  echo "STAGE=수집중  pid=$(cat "${COLLECT_PID}")  진척=$(data_episodes)/${TARGET_EP}ep"
  tail -1 "${LOG_DIR}/cop_data_collect.log" 2>/dev/null || true
  exit 0
fi

# ── 2. 학습 진행중 ──
if pid_alive "${TRAIN_PID}"; then
  echo "STAGE=학습중"
  bash "${ROOT}/scripts/check_act_train.sh" 2>/dev/null | head -5 || true
  exit 0
fi

# ── 3. 데이터 부족 → closed-loop 수집 시작 ──
EP="$(data_episodes)"
if [[ "${EP}" -lt "${TARGET_EP}" ]]; then
  echo "STAGE=수집시작  (현재 ${EP} < 목표 ${TARGET_EP}ep) — closed-loop expert"
  bash "${ROOT}/scripts/cop_start_data_collect.sh" "${TARGET_EP}" || echo "  ⚠ 수집 시작 실패"
  exit 0
fi

# ── 4. 데이터 준비됨 & 이 데이터로 미학습 → ACT 재학습 ──
DATA_SIG="$(sig "${DATA_DIR}/meta/info.json")"
if [[ ! -f "${TRAINED_MARK}" || "$(cat "${TRAINED_MARK}" 2>/dev/null || echo x)" != "${DATA_SIG}" ]]; then
  echo "STAGE=학습시작  (closed-loop 데이터 ${EP}ep 로 ACT 재학습, ${EPOCHS}epoch)"
  export COP_DATASET_ROOT="${DATA_DIR}"
  if bash "${ROOT}/scripts/start_act_train.sh" --epochs "${EPOCHS}" --no-resume; then
    echo "${DATA_SIG}" > "${TRAINED_MARK}"
  else
    echo "  ⚠ 학습 시작 실패"
  fi
  exit 0
fi

# ── 5. 학습 완료 & 이 체크포인트 미측정 → rollout 성공률 측정 ──
# 측정 기준 = 최신 체크포인트(render_act_rollout 가 실제 사용). models/act_phase1.pt 별도저장 의존 X.
LATEST_CKPT="$(ls -dt "${ROOT}"/checkpoints/act/epoch_*/ 2>/dev/null | head -1 | sed 's:/$::')"
MODEL_SIG="$(sig "${LATEST_CKPT}")"
if [[ -n "${LATEST_CKPT}" && ( ! -f "${MEASURED_MARK}" || "$(cat "${MEASURED_MARK}" 2>/dev/null || echo x)" != "${MODEL_SIG}" ) ]]; then
  echo "STAGE=측정  (최신 체크포인트 ${LATEST_CKPT##*/} rollout 성공률, closed-loop 정합 씬)"
  if "${PY}" "${ROOT}/scripts/render_act_rollout.py" --rollouts 10 > "${ROLLOUT_LOG}" 2>&1; then
    echo "${MODEL_SIG}" > "${MEASURED_MARK}"
    grep -iE "success_rate|성공률" "${ROLLOUT_LOG}" | tail -2 || tail -2 "${ROLLOUT_LOG}"
  else
    echo "  ⚠ 측정 실패 — 로그: ${ROLLOUT_LOG}"; tail -3 "${ROLLOUT_LOG}" 2>/dev/null || true
  fi
  exit 0
fi

# ── 6. 측정 완료 → 수렴 판정 ──
RATE="$(grep -oE '"?success_rate"?[: ]+[0-9.]+' "${ROLLOUT_LOG}" 2>/dev/null | grep -oE '[0-9.]+' | tail -1 || echo '?')"
echo "STAGE=완료/유지  데이터 ${EP}ep · 최종 성공률=${RATE} (목표 ${TARGET_RATE})"
echo "  한 사이클 완료. 성공률 미달이면 COP_TARGET_EP 상향 또는 데이터 재수집(마커 삭제)으로 다음 사이클 트리거."
exit 0
