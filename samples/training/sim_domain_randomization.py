"""Phase 2 W1 — Domain Randomization 기반 모듈.

Sim2Real 격차 축소를 위해 매 에피소드(또는 매 reset) 시뮬 외형/물리를 무작위화한다.
세 축을 무작위화한다 (PHASE_ROADMAP Phase 2 W1: 조명 / 마찰 / 카메라 노이즈):
  1. 조명  — light diffuse/ambient 강도 + 광원 위치 지터
  2. 마찰  — geom 슬라이딩 마찰계수 곱셈 지터 (테이블/큐브/바닥/팔)
  3. 카메라 — 렌더된 RGB 에 가우시안 센서 노이즈 추가

설계 원칙: 모델 로드 후 model.* 배열을 in-place 수정 → renderer 가 그대로 반영.
다음 단계(W2 zero-shot 추론)에서 sim_data_collector / render_act_rollout 가 이 모듈을 import 해
reset 마다 randomize_scene() 을 호출하도록 연결한다.

headless 전용 (mujoco.Renderer). viewer 호출 없음.
"""
import os
import numpy as np
import mujoco as mj

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCENE_PATH = os.path.join(BASE, "SO-ARM100/Simulation/SO101/scene_grasp_pads.xml")

# 무작위화 범위 (Sim2Real 기본값 — 실측 카메라/물성 수신 시 좁힐 수 있음)
DR_RANGES = {
    "light_diffuse": (0.4, 0.8),     # 기본 0.6 근처
    "light_ambient": (0.2, 0.45),    # 기본 0.3 근처
    "light_pos_xy_jitter": 0.5,      # 광원 XY 위치 ±m
    "friction_scale": (0.7, 1.3),    # 슬라이딩 마찰 곱셈 배수
    "camera_noise_std": (2.0, 10.0), # 0-255 RGB 가우시안 노이즈 표준편차
}


def snapshot_baseline(model):
    """DR 적용 전 원본 배열을 캐시한다.

    수집기/측정기는 model 을 한 번만 로드하고 매 reset(mj_resetData)마다 재사용한다.
    friction 은 곱셈(*=), light_pos 는 덧셈(+=) 이라 restore 없이 매번 randomize 하면
    누적된다 → 매 reset 마다 restore_baseline() 후 randomize_scene() 을 호출한다.
    (self_test 는 매 샘플 모델을 새로 로드하므로 이 캐시가 필요없다.)
    """
    return {
        "geom_friction": model.geom_friction.copy(),
        "light_diffuse": model.light_diffuse.copy(),
        "light_ambient": model.light_ambient.copy(),
        "light_pos": model.light_pos.copy(),
    }


def restore_baseline(model, baseline):
    """snapshot_baseline() 로 캐시한 원본 배열을 model 에 되돌린다 (누적 방지)."""
    model.geom_friction[:] = baseline["geom_friction"]
    model.light_diffuse[:] = baseline["light_diffuse"]
    model.light_ambient[:] = baseline["light_ambient"]
    model.light_pos[:] = baseline["light_pos"]


DR_AXES = ("light", "friction", "camera")


def randomize_scene(model, rng, axes=None):
    """model 의 조명·마찰을 in-place 무작위화하고 적용된 카메라 노이즈 std 를 반환.

    조명/마찰은 model 배열을 직접 수정하므로 다음 renderer.update_scene() 에 반영된다.
    카메라 노이즈는 렌더 결과에 적용해야 하므로 std 만 반환하고 apply_camera_noise() 가 사용한다.

    axes: 무작위화할 축 부분집합 (기본 3축 전부). 단일 축 ablation 측정용 —
    비활성 축은 원본값 유지(카메라 노이즈 std=0). 큐브 위치 rng 는 별도 스트림이라 불변.
    """
    axes = DR_AXES if axes is None else axes
    applied = {}

    # 1. 조명 — 모든 광원의 diffuse/ambient 강도 + 위치 지터
    if "light" in axes and model.nlight > 0:
        diff = rng.uniform(*DR_RANGES["light_diffuse"])
        amb = rng.uniform(*DR_RANGES["light_ambient"])
        model.light_diffuse[:] = diff
        model.light_ambient[:] = amb
        j = DR_RANGES["light_pos_xy_jitter"]
        model.light_pos[:, 0] += rng.uniform(-j, j, size=model.nlight)
        model.light_pos[:, 1] += rng.uniform(-j, j, size=model.nlight)
        applied["light_diffuse"] = round(float(diff), 3)
        applied["light_ambient"] = round(float(amb), 3)

    # 2. 마찰 — 모든 geom 의 슬라이딩 마찰계수(col 0) 곱셈 지터
    if "friction" in axes:
        fscale = rng.uniform(*DR_RANGES["friction_scale"])
        model.geom_friction[:, 0] *= fscale
        applied["friction_scale"] = round(float(fscale), 3)

    # 3. 카메라 노이즈 std (렌더 후 적용) — 비활성 시 0
    noise_std = rng.uniform(*DR_RANGES["camera_noise_std"]) if "camera" in axes else 0.0
    applied["camera_noise_std"] = round(float(noise_std), 3)

    return applied


def apply_camera_noise(img, noise_std, rng):
    """렌더된 uint8 RGB 이미지에 가우시안 센서 노이즈를 더해 반환."""
    noisy = img.astype(np.float32) + rng.normal(0.0, noise_std, size=img.shape)
    return np.clip(noisy, 0, 255).astype(np.uint8)


def _self_test(n_samples=8, seed=0):
    """N 샘플을 무작위화·렌더하여 적용 범위를 검증하고 샘플 프레임을 저장."""
    from PIL import Image

    out_dir = os.path.join(BASE, "research/simulation/dr_samples")
    os.makedirs(out_dir, exist_ok=True)
    rng = np.random.default_rng(seed)

    cam_id = -1
    applied_log = []
    for i in range(n_samples):
        # 매 샘플 모델을 새로 로드해야 누적 곱셈을 피한다(독립 무작위화).
        model = mj.MjModel.from_xml_path(SCENE_PATH)
        data = mj.MjData(model)
        if cam_id == -1:
            cam_id = mj.mj_name2id(model, mj.mjtObj.mjOBJ_CAMERA, "overhead_camera")
            if cam_id == -1:
                raise RuntimeError("overhead_camera not found in scene")

        applied = randomize_scene(model, rng)
        mj.mj_forward(model, data)

        renderer = mj.Renderer(model, height=480, width=640)
        renderer.update_scene(data, camera=cam_id)
        img = renderer.render()
        img = apply_camera_noise(img, applied["camera_noise_std"], rng)
        renderer.close()

        Image.fromarray(img).save(os.path.join(out_dir, f"dr_sample_{i:02d}.png"))
        applied_log.append(applied)
        print(f"[{i:02d}] {applied}")

    # 적용 범위 요약 (검증 메트릭)
    keys = ["light_diffuse", "light_ambient", "friction_scale", "camera_noise_std"]
    print("\n=== 적용 범위 (min/max over %d samples) ===" % n_samples)
    summary = {}
    for k in keys:
        vals = [a[k] for a in applied_log if k in a]
        if vals:
            summary[k] = {"min": min(vals), "max": max(vals)}
            print(f"  {k:18s}: {min(vals):.3f} ~ {max(vals):.3f}")
    print(f"\n샘플 프레임 {n_samples}장 저장: {out_dir}")
    return summary


if __name__ == "__main__":
    _self_test()
