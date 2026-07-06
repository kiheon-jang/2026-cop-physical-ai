#!/Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv/bin/python
"""히어로 포스터 1장 생성 — 로봇팔이 큐브를 든 시네마틱 3/4 프레임.

바닥 씬(scene_grasp_floor.xml, 받침대 없음)에서 closed-loop expert 를 성공까지 실행한 뒤,
3/4 자유 카메라로 렌더 → JPEG → base64 → dashboard/hero_poster.txt.
build.py 가 이걸 읽어 data.json 의 web3d.hero_poster_b64 로 인라인한다(런타임 WebGL 0, CDN 0).

사용: .venv/bin/python3 scripts/export_hero_poster.py
"""
import base64
import io
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path("/Volumes/MARK_DATA/dev/2026-cop-physical-ai")
OUT = ROOT / "dashboard" / "hero_poster.txt"
sys.path.insert(0, str(ROOT / "samples" / "training"))

import sim_data_collector as C  # noqa: E402

C.TABLE_TOP = 0.0  # 바닥 배치
FLOOR_XML = str(ROOT / "SO-ARM100" / "Simulation" / "SO101" / "scene_grasp_floor.xml")


def main() -> None:
    import mujoco
    from PIL import Image

    expert = C.GraspExpert(FLOOR_XML)
    m, d = expert.m, expert.d

    # 큐브가 확실히 들린 성공 에피소드를 찾을 때까지 시도 (시드 고정)
    import random
    random.seed(7)
    best_lift, best_qpos = 0.0, None
    for _ in range(6):
        cube_xy = C.CUBE_BASE_XY + np.array([random.uniform(-0.01, 0.01),
                                             random.uniform(-0.01, 0.01)])
        maxlift, _ = expert.run_episode(cube_xy)
        if maxlift > best_lift:
            best_lift = maxlift
            best_qpos = d.qpos.copy()
        if maxlift >= 0.05:
            break
    if best_qpos is not None:
        d.qpos[:] = best_qpos
        mujoco.mj_forward(m, d)
    print(f"[poster] 큐브 리프트 {best_lift*1000:.1f}mm 프레임 렌더")

    # 시네마틱 3/4 자유 카메라
    W, H = 1100, 720
    renderer = mujoco.Renderer(m, height=H, width=W)
    cam = mujoco.MjvCamera()
    mujoco.mjv_defaultCamera(cam)
    cam.lookat[:] = [0.10, 0.0, 0.085]
    cam.distance = float(os.environ.get("POSTER_DIST", 0.52))
    cam.azimuth = float(os.environ.get("POSTER_AZ", 40))
    cam.elevation = float(os.environ.get("POSTER_EL", -12))
    opt = mujoco.MjvOption()
    mujoco.mjv_defaultOption(opt)
    renderer.update_scene(d, camera=cam, scene_option=opt)
    rgb = renderer.render()
    renderer.close()

    img = Image.fromarray(rgb).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode()
    OUT.write_text(b64, encoding="utf-8")
    print(f"[poster] {OUT.relative_to(ROOT)}  {len(b64)//1024}KB (base64)  {W}x{H}")


if __name__ == "__main__":
    main()
