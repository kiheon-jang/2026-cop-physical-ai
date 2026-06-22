#!/bin/bash
cd /Volumes/MARK_DATA/dev/2026-cop-physical-ai
PY=./.venv/bin/python3
run_n() {
  script=$1; n=$2; label=$3
  echo "=== $label ($n reps) ==="
  i=1; total=0; passes=0
  while [ $i -le $n ]; do
    start=$(date +%s.%N)
    $PY $script > /tmp/out_${label}_${i}.log 2>&1
    rc=$?
    end=$(date +%s.%N)
    dur=$(awk -v s=$start -v e=$end 'BEGIN{print e-s}')
    echo "  run$i rc=$rc time=${dur}s"
    if [ $rc -eq 0 ]; then passes=$((passes+1)); fi
    total=$(awk -v t=$total -v d=$dur 'BEGIN{print t+d}')
    i=$((i+1))
  done
  avg=$(awk -v t=$total -v n=$n 'BEGIN{print t/n}')
  echo "  SUMMARY: $passes/$n pass, avg=${avg}s"
}
run_n samples/training/sim_camera_verification.py 5 camera
run_n samples/training/sim_headless_6dof_video.py 5 headless6dof
run_n samples/training/sim_pick_place.py 5 pickplace
