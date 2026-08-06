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
#   2.5) 학습 종료 확정 → pending 마커 검증(완료=승격 / 이상종료=재시도 예약)
#   3) 데이터 부족   → cop_start_data_collect.sh (closed-loop 수집, nohup)
#   4) 데이터 준비됨 & 이 데이터로 미학습 → start_act_train.sh (ACT 재학습, nohup)
#   5) 학습 완료 & 이 모델 미측정 → render_act_rollout.py (성공률 측정)
#   6) 측정 완료     → 수렴 판정 + 상태 보고
#
# 데이터셋 타겟: logs/cop_dataset_target 파일(한 줄, ROOT 상대경로)로 전환.
#   예) echo "data/episodes_cl_dr" > logs/cop_dataset_target  → 다음 실행부터 DR 사이클.
#   파일 없으면 기본 data/episodes_cl. 체크포인트는 데이터셋별 디렉터리로 격리
#   (episodes_cl=checkpoints/act 레거시 유지, episodes_cl_dr=checkpoints/act_cl_dr)
#   → 재학습이 기존 baseline 모델을 덮어쓰지 않는다.
#
# 마커 형식: "<데이터셋 basename>:<서명>" (2026-07-06 개정. 구형식=서명만 → 자동 불일치로 안전).
# 서명: 디렉터리는 내부 파일 최신 mtime (save_pretrained 의 in-place 덮어쓰기 감지).
#
# 출력: "CoP 시뮬 파이프라인" 상태블록 → cron 이 research-log + 아침 메일에 그대로 append.
# 네이밍: 모든 산출물 cop_ 접두 (다른 프로젝트 잡과 격리).
set -uo pipefail

ROOT="/Volumes/MARK_DATA/dev/2026-cop-physical-ai"
PY="${ROOT}/.venv/bin/python3"
LOG_DIR="${ROOT}/logs"

TARGET_EP="${COP_TARGET_EP:-50}"        # 목표 성공 에피소드 수
TARGET_RATE="${COP_TARGET_RATE:-0.90}"  # 목표 rollout 성공률
# 2026-07-19 자가치유: floor 재학습이 12-run 연속 이상종료. 결정적 규명 = 고정 벽시계(~04:04)
# 외부 SIGKILL(RSS·mps_mem·FD 전부 평탄, epoch↔벽시계 교락이 pid5069 느린 epoch 로 풀림 = ep49@04:04
# vs 이전 ep57@04:04). 100epoch×~368s=~10h 는 23:00→04:04(5h) 창에 물리적으로 못 들어감 = 진짜 deadlock.
# 창 안에 완주하도록 목표 하향(42×~400s(최악)=~03:41<04:04). 04:04 killer 규명(log show/launchctl,
# sandbox 차단)되면 full-epoch 로 복원. COP_EPOCHS override 유지. ponytail: 창 크기 knob.
EPOCHS="${COP_EPOCHS:-42}"

# ── 데이터셋 타겟 결정 (파일 기반 — cron 은 env 를 안 넘기므로 영속 상태는 파일로) ──
DATASET_TARGET_FILE="${LOG_DIR}/cop_dataset_target"
if [[ -f "${DATASET_TARGET_FILE}" ]]; then
  _T="$(head -1 "${DATASET_TARGET_FILE}" | tr -d '[:space:]')"
  [[ "${_T}" == /* ]] || _T="${ROOT}/${_T}"
  DATA_DIR="${_T}"
else
  DATA_DIR="${ROOT}/data/episodes_cl"
fi
DS_BASE="${DATA_DIR##*/}"
# S1(리셋버튼)은 pick-place 와 수집기·관측(2카메라)·측정기가 다르다 → 스테이지별 분기 (아래).
[[ "${DS_BASE}" == "episodes_s1" ]] && IS_S1=1 || IS_S1=0

# ── 체크포인트 디렉터리: 데이터셋별 격리 (episodes_cl 은 레거시 경로 유지) ──
if [[ "${DS_BASE}" == "episodes_cl" ]]; then
  CKPT_DIR="${ROOT}/checkpoints/act"
elif [[ "${IS_S1}" == 1 ]]; then
  CKPT_DIR="${ROOT}/checkpoints/act_s1_sim"   # 수동 W3 학습이 이 경로 사용 (규칙상 act_s1 아님)
else
  CKPT_DIR="${ROOT}/checkpoints/act_${DS_BASE#episodes_}"
fi

# ── 씬: 데이터셋에 정합 (수집·측정이 같은 씬을 쓰도록 export) ──
case "${DS_BASE}" in
  *floor*) COP_SCENE="${ROOT}/SO-ARM100/Simulation/SO101/scene_grasp_floor.xml" ;;
  *s1*)    COP_SCENE="${ROOT}/sim/assets/pcb_reset_scene.xml" ;;  # S1 측정기는 twin 자체 로드 — 참고용
  *)       COP_SCENE="${ROOT}/SO-ARM100/Simulation/SO101/scene_grasp_pads.xml" ;;
esac
export COP_SCENE

COLLECT_PID="${LOG_DIR}/cop_data_collect.pid"
TRAIN_PID="${LOG_DIR}/act_train.pid"
TRAINED_MARK="${LOG_DIR}/cop_trained_on.marker"     # 학습에 쓴 데이터 서명 ("ds:sig")
TRAINED_PENDING="${TRAINED_MARK}.pending"           # 학습 '시작' 기록 — 완료 검증 후 승격
MEASURED_MARK="${LOG_DIR}/cop_measured.marker"      # 측정한 모델 서명 ("ds:sig")
ROLLOUT_LOG="${LOG_DIR}/cop_rollout.log"
METRICS_LOG="${LOG_DIR}/act_train_metrics.jsonl"

cd "${ROOT}"
mkdir -p "${LOG_DIR}"

# pid 파일이 가리키는 프로세스가 살아있고, 커맨드가 기대 패턴과 일치하나.
# 죽었거나 PID 재사용(다른 프로세스)이면 stale pid 파일 정리 후 실패 반환.
pid_alive() {
  local f="$1" pat="${2:-}"
  [[ -f "$f" ]] || return 1
  local p; p="$(cat "$f" 2>/dev/null || true)"
  if [[ -z "$p" ]] || ! kill -0 "$p" 2>/dev/null; then
    rm -f "$f"; return 1
  fi
  if [[ -n "$pat" ]] && ! ps -p "$p" -o command= 2>/dev/null | grep -q "$pat"; then
    rm -f "$f"; return 1
  fi
  return 0
}
# LeRobot 데이터셋의 에피소드 수
data_episodes() {
  [[ -f "${DATA_DIR}/meta/info.json" ]] || { echo 0; return; }
  "${PY}" -c "import json,sys
try: print(json.load(open('${DATA_DIR}/meta/info.json')).get('total_episodes',0))
except Exception: print(0)" 2>/dev/null || echo 0
}
# 서명: 파일=mtime, 디렉터리=내부 파일 최신 mtime (in-place 덮어쓰기 감지)
sig() {
  local m
  if [[ -d "$1" ]]; then
    m="$(find "$1" -type f -exec stat -f '%m' {} + 2>/dev/null | sort -n | tail -1)"
  else
    m="$(stat -f '%m' "$1" 2>/dev/null)"
  fi
  echo "${m:-0}"
}
# 학습 완료 검증: metrics jsonl 마지막 줄이 (해당 데이터셋, 마지막 epoch, pending 이후) 인가
train_completed() {
  local pending_mtime; pending_mtime="$(stat -f '%m' "${TRAINED_PENDING}" 2>/dev/null || echo 0)"
  "${PY}" -c "
import json, sys
try:
    last = open('${METRICS_LOG}').readlines()[-1]
    m = json.loads(last)
    ok = (m.get('epoch') == ${EPOCHS} - 1
          and m.get('timestamp', 0) > ${pending_mtime}
          and m.get('dataset', '${DS_BASE}') == '${DS_BASE}')
    sys.exit(0 if ok else 1)
except Exception:
    sys.exit(1)" 2>/dev/null
}

echo "════════ 🤖 CoP Physical AI 시뮬 파이프라인 ($(date '+%Y-%m-%d %H:%M')) ════════"
echo "타겟: 데이터=${DS_BASE}  ckpt=${CKPT_DIR#${ROOT}/}"

# ── 1. 수집 진행중 ──
if pid_alive "${COLLECT_PID}" "sim_data_collector"; then
  echo "STAGE=수집중  pid=$(cat "${COLLECT_PID}")  진척=$(data_episodes)/${TARGET_EP}ep"
  tail -1 "${LOG_DIR}/cop_data_collect.log" 2>/dev/null || true
  exit 0
fi

# ── 2. 학습 진행중 ──
if pid_alive "${TRAIN_PID}" "train_act"; then
  echo "STAGE=학습중"
  COP_CKPT_DIR="${CKPT_DIR}" bash "${ROOT}/scripts/check_act_train.sh" 2>/dev/null | head -5 || true
  exit 0
fi

# ── 2.5. 학습 종료 확정 (pending 검증 → 완료면 승격, 이상종료면 재시도 예약) ──
if [[ -f "${TRAINED_PENDING}" ]]; then
  if train_completed; then
    mv "${TRAINED_PENDING}" "${TRAINED_MARK}"
    echo "학습완료 확정 (${DS_BASE}, ${EPOCHS}epoch) → 측정 단계로 진행"
    # fall through — 같은 실행에서 stage 5 측정까지 진행
  else
    rm -f "${TRAINED_PENDING}"
    echo "⚠ 학습 이상종료 감지 (${DS_BASE} — metrics 마지막 epoch 미달) → 재학습 재시도 예약"
    tail -3 "${LOG_DIR}/act_train.log" 2>/dev/null || true
    # fall through — stage 4 가 재학습을 다시 시작
  fi
fi

# ── 3. 데이터 부족 → closed-loop 수집 시작 ──
EP="$(data_episodes)"
if [[ "${EP}" -lt "${TARGET_EP}" ]]; then
  # S1 은 합성 데이터(고정 100ep) — pick-place 수집기로 채우면 episodes_s1 오염. 미실행 보류.
  if [[ "${IS_S1}" == 1 ]]; then
    echo "⚠ STAGE=보류  S1 합성 데이터 부족(${EP}<${TARGET_EP}ep) — S1 수집기=samples/training/sim_pcb_reset_collector.py (별도). pick-place 수집기 미실행 (episodes_s1 보호)."
    exit 0
  fi
  # 가드: info.json 이 존재하는데 0 이 나오면 일시적 읽기 실패 가능성 — 수집(=기존 데이터
  # 대피 후 재수집) 을 시작하지 않는다 (운영 데이터셋 보호).
  if [[ "${EP}" -eq 0 && -f "${DATA_DIR}/meta/info.json" ]]; then
    echo "⚠ STAGE=보류  데이터 카운트 실패 의심 (info.json 존재하나 0 반환) — 수집 시작 안 함"
    exit 0
  fi
  echo "STAGE=수집시작  (현재 ${EP} < 목표 ${TARGET_EP}ep) — closed-loop expert"
  COP_DATA_DIR="${DATA_DIR}" bash "${ROOT}/scripts/cop_start_data_collect.sh" "${TARGET_EP}" || echo "  ⚠ 수집 시작 실패"
  exit 0
fi

# ── 4. 데이터 준비됨 & 이 데이터로 미학습 → ACT 재학습 ──
DATA_SIG="${DS_BASE}:$(sig "${DATA_DIR}/meta/info.json")"
if [[ ! -f "${TRAINED_MARK}" || "$(cat "${TRAINED_MARK}" 2>/dev/null || echo x)" != "${DATA_SIG}" ]]; then
  echo "STAGE=학습시작  (${DS_BASE} ${EP}ep 로 ACT 재학습, ${EPOCHS}epoch → ${CKPT_DIR#${ROOT}/})"
  export COP_DATASET_ROOT="${DATA_DIR}"
  export COP_CKPT_DIR="${CKPT_DIR}"
  if [[ "${IS_S1}" == 1 ]]; then          # S1 2카메라 계약 — 없으면 1카메라로 학습돼 데이터와 형상 불일치
    export COP_CAMERA_KEYS="top,closeup"
    export COP_DATASET_REPO_ID="local/pcb_reset_sim"
  fi
  if bash "${ROOT}/scripts/start_act_train.sh" --epochs "${EPOCHS}" --no-resume; then
    echo "${DATA_SIG}" > "${TRAINED_PENDING}"   # 완료 검증(stage 2.5) 후 TRAINED_MARK 로 승격
  else
    echo "  ⚠ 학습 시작 실패"
  fi
  exit 0
fi

# ── 5. 학습 완료 & 이 체크포인트 미측정 → rollout 성공률 측정 ──
# 측정 기준 = 최신 체크포인트의 내부 파일 서명 (in-place 덮어쓰기도 감지).
LATEST_CKPT="$(ls -d "${CKPT_DIR}"/epoch_*/ 2>/dev/null | sort | tail -1 | sed 's:/$::')"
MODEL_SIG="${DS_BASE}:$(sig "${LATEST_CKPT}")"
if [[ -n "${LATEST_CKPT}" && ( ! -f "${MEASURED_MARK}" || "$(cat "${MEASURED_MARK}" 2>/dev/null || echo x)" != "${MODEL_SIG}" ) ]]; then
  echo "STAGE=측정  (최신 체크포인트 ${LATEST_CKPT##*/} rollout 성공률)"
  export COP_CKPT_DIR="${CKPT_DIR}"
  if [[ "${IS_S1}" == 1 ]]; then
    MEASURE_ARGS=( "${ROOT}/scripts/render_act_rollout_s1.py" )        # LED latch 4-seed, S1 산출물
  else
    MEASURE_ARGS=( "${ROOT}/scripts/render_act_rollout.py" --rollouts 10 )
  fi
  if "${PY}" "${MEASURE_ARGS[@]}" > "${ROLLOUT_LOG}" 2>&1; then
    echo "${MODEL_SIG}" > "${MEASURED_MARK}"
    grep -iE "success_rate|성공률" "${ROLLOUT_LOG}" | tail -2 || tail -2 "${ROLLOUT_LOG}"
  else
    echo "  ⚠ 측정 실패 — 로그: ${ROLLOUT_LOG}"; tail -3 "${ROLLOUT_LOG}" 2>/dev/null || true
  fi
  exit 0
fi

# ── 6. 측정 완료 → 수렴 판정 (+ 예약된 다음 사이클 자동 전환) ──
RATE="$(grep -oE '"?success_rate"?[: ]+[0-9.]+' "${ROLLOUT_LOG}" 2>/dev/null | grep -oE '[0-9.]+' | tail -1 || echo '?')"
echo "STAGE=완료/유지  데이터 ${DS_BASE} ${EP}ep · 최종 성공률=${RATE} (목표 ${TARGET_RATE})"

# 다음 사이클 예약(cop_dataset_target.next): 현 사이클이 완주(측정까지)한 뒤에만 전환.
# 전환 후 exec 로 1회 재평가 → 같은 실행에서 새 사이클의 첫 단계(보통 학습시작)까지 전진.
NEXT_TARGET="${DATASET_TARGET_FILE}.next"
if [[ -f "${NEXT_TARGET}" ]]; then
  NEXT_DS="$(head -1 "${NEXT_TARGET}" | tr -d '[:space:]')"
  if [[ -n "${NEXT_DS}" && "${NEXT_DS}" != "$(cat "${DATASET_TARGET_FILE}" 2>/dev/null || true)" ]]; then
    mv "${NEXT_TARGET}" "${DATASET_TARGET_FILE}"
    echo "  ▶ 예약된 다음 사이클로 전환: ${NEXT_DS} — 재평가 시작"
    exec bash "$0"   # .next 소거됨 → 재귀 1회로 종결
  fi
  rm -f "${NEXT_TARGET}"
fi
echo "  한 사이클 완료. 다음 사이클: logs/cop_dataset_target(.next) 전환 또는 데이터 재수집(마커 삭제)."
exit 0
