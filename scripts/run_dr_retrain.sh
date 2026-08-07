#!/usr/bin/env bash
# DR 재학습 드라이버 (② — DR 강건성 0.45 정당화 후속).
#   STAGE1: DR 재수집(조명/마찰/카메라 3축) → data/episodes_s1_dr (100ep, seed42=nominal 과 동일 배치)
#   STAGE2: cold-start 학습 30ep → checkpoints/act_s1_sim_dr (nominal act_s1_sim 절대 안 건드림)
# 측정(nominal+--dr)은 학습 완료 후 수동 — render 산출물이 RUN_TAG 고정이라 라이브 nominal summary 를 덮어쓰기 때문.
#
# 반드시 start_new_session 으로 디태치 실행할 것 (04:04 ai.hermes.autoupdate 프로세스그룹 SIGKILL 생존).
# 진행 확인: tail -f logs/dr_retrain.log ; cat logs/dr_retrain.status
set -uo pipefail
ROOT="/Volumes/MARK_DATA/dev/2026-cop-physical-ai"
PY="$ROOT/.venv/bin/python3"
LOG="$ROOT/logs/dr_retrain.log"
STATUS="$ROOT/logs/dr_retrain.status"
cd "$ROOT"
export PYTORCH_ENABLE_MPS_FALLBACK=1
ts(){ date '+%Y-%m-%d %H:%M:%S'; }

echo "RUNNING collect $(ts)" > "$STATUS"
echo "[$(ts)] === DR RETRAIN DRIVER START (pid=$$) ===" >> "$LOG"

# --- STAGE 1: DR 재수집 ---
echo "[$(ts)] STAGE1 DR collect 100ep(3축) -> data/episodes_s1_dr" >> "$LOG"
COP_COLLECT_DR=1 COP_COLLECT_DR_AXES=light,friction,camera \
  "$PY" samples/training/sim_pcb_reset_collector.py \
  --root "$ROOT/data/episodes_s1_dr" --episodes 100 --seed 42 >> "$LOG" 2>&1
rc=$?
if [ $rc -ne 0 ]; then
  echo "FAILED collect rc=$rc $(ts)" > "$STATUS"
  echo "[$(ts)] STAGE1 FAIL rc=$rc (yield<100 가능 — 로그 확인)" >> "$LOG"; exit 1
fi

# --- STAGE 2: cold-start 학습 30ep ---
echo "RUNNING train $(ts)" > "$STATUS"
echo "[$(ts)] STAGE2 train 30ep -> checkpoints/act_s1_sim_dr" >> "$LOG"
COP_DATASET_ROOT="$ROOT/data/episodes_s1_dr" \
COP_DATASET_REPO_ID=local/pcb_reset_sim \
COP_CAMERA_KEYS=top,closeup \
COP_CKPT_DIR="$ROOT/checkpoints/act_s1_sim_dr" \
  "$PY" scripts/train_act.py --epochs 30 --device mps >> "$LOG" 2>&1
rc=$?
if [ $rc -ne 0 ]; then
  echo "FAILED train rc=$rc $(ts)" > "$STATUS"
  echo "[$(ts)] STAGE2 FAIL rc=$rc" >> "$LOG"; exit 1
fi

echo "DONE $(ts) — 측정: COP_CKPT_DIR=checkpoints/act_s1_sim_dr .venv/bin/python3 scripts/render_act_rollout_s1.py [--dr] --device cpu" > "$STATUS"
echo "[$(ts)] === DONE — 측정 대기(수동, nominal+--dr 로 0.45 개선폭 확인) ===" >> "$LOG"
