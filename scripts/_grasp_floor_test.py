#!/Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv/bin/python
"""바닥 파지 검증 — "받침대(0.16m) 없이는 못 집는가?" (2026-07-06)

운영 closed-loop expert(sim_data_collector.GraspExpert, 코드 무수정)를
받침대 없는 씬(scene_grasp_floor.xml, 큐브 z=0.015 바닥)에서 그대로 실행해
성공률을 잰다. expert 는 전부 큐브 xpos 추종(cube-relative)이라 씬 교체 +
배치 상수(TABLE_TOP→0)만 바꾸면 동작한다.

비교 기준: 받침대 씬 expert 성공률 75~88% (yield 86~91%).
사용: .venv/bin/python3 scripts/_grasp_floor_test.py [에피소드수=10] [seed=42]
"""

import sys
from pathlib import Path

import numpy as np

ROOT = Path("/Volumes/MARK_DATA/dev/2026-cop-physical-ai")
sys.path.insert(0, str(ROOT / "samples" / "training"))

import sim_data_collector as C  # noqa: E402

C.TABLE_TOP = 0.0  # 바닥 배치 (reset_with_cube 가 TABLE_TOP + HALF 에 큐브를 놓음)
FLOOR_XML = str(ROOT / "SO-ARM100" / "Simulation" / "SO101" / "scene_grasp_floor.xml")


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    rng = np.random.default_rng(seed)

    expert = C.GraspExpert(FLOOR_XML)
    results = []
    for i in range(n):
        off = rng.uniform(-C.RANDOM_POS_RANGE, C.RANDOM_POS_RANGE, size=2)
        cube_xy = C.CUBE_BASE_XY + off
        maxlift, tries = expert.run_episode(cube_xy)
        ok = maxlift >= C.SUCCESS_LIFT
        results.append(ok)
        print(f"[{i+1}/{n}] {'성공' if ok else '실패'}  lift={maxlift*1000:5.1f}mm "
              f"재시도={tries}  cube=({cube_xy[0]:.3f},{cube_xy[1]:.3f})", flush=True)

    sr = sum(results) / len(results)
    print(f"\n바닥 파지(받침대 없음, 큐브 z=0.015) 성공률: {sum(results)}/{n} = {sr:.0%}"
          f"  (기준: 받침대 씬 expert 75~88%)")


if __name__ == "__main__":
    main()
