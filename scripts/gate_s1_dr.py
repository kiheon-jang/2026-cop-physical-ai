#!/Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv/bin/python
"""S1 DR 게이트 — DR 학습 정책이 DR 교란을 견디는지 측정 (운영 산출물 불변).

왜 필요한가
-----------
RS232 트랙에 DR(도메인 랜덤화)을 배선하고 32.5시간 재학습을 돌릴지 결정해야 한다.
근거가 필요하다: 2단계(S1)에서 DR 미학습 정책은 3축 DR 교란에서 0.925 → 약 0.45 로
무너진 측정이 있다. 그런데 **DR 로 학습한 체크포인트(`checkpoints/act_s1_sim_dr/`)가
그 교란에서 회복하는지는 측정된 적이 없다.**

회복이 안 보이면 RS232 DR 재학습에 32.5시간을 쓸 근거가 없다. 10분으로 그걸 가른다.

왜 래퍼인가
-----------
`scripts/render_act_rollout_s1.py` 는 `--out-dir` 인자가 없고 `OUT_DIR`(45행)이 운영 경로
`research/simulation/inference_progress` 로 하드코딩돼 있다. 그대로 실행하면 대시보드가 읽는
`rollout_summary_s1*.json` 을 덮어쓴다. 측정기를 고치지 않고 모듈 전역만 바꿔 우회한다.

사용
----
  # DR 학습 정책 × DR 교란 (게이트 본체)
  .venv/bin/python3 scripts/gate_s1_dr.py --out-dir /tmp/gate_dr_on \
      --checkpoint checkpoints/act_s1_sim_dr/epoch_0029 --dr --seeds 42 --rollouts 10

  # 같은 정책 × 교란 없음 (기준점)
  .venv/bin/python3 scripts/gate_s1_dr.py --out-dir /tmp/gate_dr_off \
      --checkpoint checkpoints/act_s1_sim_dr/epoch_0029 --seeds 42 --rollouts 10

--out-dir 는 필수다. 운영 디렉터리를 주면 거부한다.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "samples" / "training"))

ap = argparse.ArgumentParser(add_help=False)
ap.add_argument("--out-dir", type=str, required=True,
                help="산출물 디렉터리 (운영 inference_progress 밖이어야 함)")
known, passthrough = ap.parse_known_args()

out = Path(known.out_dir).resolve()
operational = (ROOT / "research" / "simulation" / "inference_progress").resolve()
if out == operational or operational in out.parents:
    sys.exit(f"거부: --out-dir 가 운영 디렉터리 안이다 ({out}). 운영 S1 수치를 덮어쓴다.")
out.mkdir(parents=True, exist_ok=True)

import render_act_rollout_s1 as M  # noqa: E402

M.OUT_DIR = out                     # 측정기 파일은 건드리지 않고 전역만 교체
print(f"[gate] 산출물 → {out}", flush=True)

M.main(passthrough)
