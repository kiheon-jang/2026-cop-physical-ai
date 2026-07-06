#!/Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv/bin/python
"""
ACT 정책 rollout — 학습된 모델을 MuJoCo pick-place 시뮬에서 실행.

두 가지 산출물을 만든다:
  1) rollout 영상 → research/simulation/inference_progress/inference_epoch_{NN}_{date}.mp4
     (대시보드 build_inference_progress() 가 이 폴더를 스캔)
  2) Pick 성공률 → 큐브를 Z+50mm 이상 들어올린 rollout 비율 (Phase 1 완료 기준 90%)

관측/액션 포맷은 samples/training/sim_data_collector.py 와 1:1 정합해야 한다 (정책이 그 포맷으로 학습됨):
  - observation.images.top : overhead_camera 렌더 → [::-1] 상하반전 → (3,480,640) float[0,1]
  - observation.state      : qpos[:6] (6 관절)
  - action(정책 출력)       : ctrl[:6]

사용:
  .venv/bin/python3 scripts/render_act_rollout.py                          # 최신 ckpt, 10 rollouts, cpu
  .venv/bin/python3 scripts/render_act_rollout.py --checkpoint checkpoints/act/epoch_0099 --rollouts 20
  .venv/bin/python3 scripts/render_act_rollout.py --device cpu             # 학습(MPS)과 자원 경합 회피(기본 cpu)
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path("/Volumes/MARK_DATA/dev/2026-cop-physical-ai")
# closed-loop 학습 씬과 1:1 정합 — 측정이 유효하려면 학습 씬/물리와 동일해야 한다.
# COP_SCENE: 드라이버가 데이터셋에 맞는 씬을 넘긴다 (episodes_floor → scene_grasp_floor.xml).
MODEL_XML = Path(os.environ.get(
    "COP_SCENE", str(ROOT / "SO-ARM100" / "Simulation" / "SO101" / "scene_grasp_pads.xml")))
OUT_DIR = ROOT / "research" / "simulation" / "inference_progress"

# sim_data_collector.py(closed-loop) 와 동일한 상수
_CUBE_Z = 0.015 if "floor" in MODEL_XML.name else 0.175  # 바닥 vs 작업대(0.16)+half
CUBE_INITIAL_POS = np.array([0.13, 0.0, _CUBE_Z])
RANDOM_POS_RANGE = 0.02          # ±20mm (수집 분포와 동일)
SIM_FPS = 30
DATA_SAMPLE_EVERY = 17           # 정책 1 액션당 물리 스텝 수 (학습 샘플링과 동일)
LIFT_THRESHOLD_M = 0.040         # 성공: 큐브 +40mm 들어올림 (수집기 성공기준과 동일)
ARM_FORCERANGE = 3.0             # 12V STS3215 팔로워 실스펙(≈2.94Nm) — 수집과 동일 물리
SETTLE_STEPS = 80                # 큐브를 작업대에 안착시키는 사전 스텝 (수집기와 동일)
N_JOINTS = 6


def find_latest_checkpoint() -> Path | None:
    # COP_CKPT_DIR: 드라이버가 데이터셋별 체크포인트 디렉터리를 지정 (기본: 운영 checkpoints/act).
    # 정렬은 내부 model.safetensors mtime — 디렉터리 mtime 은 save_pretrained 의
    # in-place 덮어쓰기를 감지하지 못한다 (epoch_0099 디렉터리 6/22 vs 내부 파일 6/25 실사례).
    ckpt_dir = Path(os.environ.get("COP_CKPT_DIR", str(ROOT / "checkpoints" / "act")))
    ckpts = sorted(
        ckpt_dir.glob("epoch_*/"),
        key=lambda p: (p / "model.safetensors").stat().st_mtime
        if (p / "model.safetensors").exists() else 0.0,
    )
    return ckpts[-1] if ckpts else None


def run_rollout(model, data, policy, renderer, cam_id, device, rng, max_frames, collect_frames,
                dr_mod=None, dr_baseline=None, dr_rng=None, dr_axes=None):
    """단일 rollout 실행. (success, max_lift_m, frames) 반환."""
    import torch
    import mujoco

    mujoco.mj_resetData(model, data)
    dr_noise_std = 0.0
    if dr_mod is not None:
        # DR-on 측정: reset 마다 원본 복원 후 무작위화 (누적 방지). 관측 RGB 에 카메라 노이즈.
        dr_mod.restore_baseline(model, dr_baseline)
        applied = dr_mod.randomize_scene(model, dr_rng, axes=dr_axes)
        mujoco.mj_setConst(model, data)
        dr_noise_std = applied["camera_noise_std"]
    # 큐브 초기 위치 랜덤 (수집과 동일 분포)
    off = rng.uniform(-RANDOM_POS_RANGE, RANDOM_POS_RANGE, size=2)
    cube_pos = CUBE_INITIAL_POS + np.array([off[0], off[1], 0.0])
    cube_jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "cube_joint")
    adr = model.jnt_qposadr[cube_jid]
    data.qpos[adr:adr + 3] = cube_pos
    data.qpos[adr + 3:adr + 7] = [1.0, 0.0, 0.0, 0.0]
    data.ctrl[:5] = 0.0
    data.ctrl[5] = 1.5               # 그리퍼 개방 (수집 초기상태와 동일)
    mujoco.mj_forward(model, data)
    for _ in range(SETTLE_STEPS):    # 큐브 작업대 안착 (수집기와 동일 패턴)
        mujoco.mj_step(model, data)

    policy.reset()
    cube_init_z = float(data.body("cube").xpos[2])
    max_lift = 0.0
    frames = []
    traj = []  # 정책 스텝별 (qpos6 + cube xyz) — 웹 3D 리플레이용

    for _ in range(max_frames):
        renderer.update_scene(data, camera=cam_id)
        rgb = renderer.render()[::-1, :, :].copy()      # 학습과 동일한 상하반전 보정
        if dr_mod is not None:
            rgb = dr_mod.apply_camera_noise(rgb, dr_noise_std, dr_rng)
        if collect_frames:
            frames.append(rgb)

        img = torch.from_numpy(rgb).permute(2, 0, 1).float().div_(255.0)  # (3,480,640) [0,1]
        state = torch.from_numpy(data.qpos[:N_JOINTS].astype(np.float32))
        batch = {
            "observation.images.top": img.unsqueeze(0).to(device),
            "observation.state": state.unsqueeze(0).to(device),
        }
        with torch.no_grad():
            action = policy.select_action(batch)        # (1,6) 비정규화 ctrl
        data.ctrl[:N_JOINTS] = action.squeeze(0).cpu().numpy()

        for _ in range(DATA_SAMPLE_EVERY):
            mujoco.mj_step(model, data)

        lift = float(data.body("cube").xpos[2]) - cube_init_z
        max_lift = max(max_lift, lift)
        traj.append(
            [round(float(q), 4) for q in data.qpos[:N_JOINTS]]
            + [round(float(x), 4) for x in data.body("cube").xpos]
        )

    return (max_lift >= LIFT_THRESHOLD_M), max_lift, frames, traj


def main(argv=None):
    p = argparse.ArgumentParser(description="ACT 정책 rollout + 성공률 측정")
    p.add_argument("--checkpoint", type=str, default=None, help="ckpt 디렉터리 (기본: 최신)")
    p.add_argument("--rollouts", type=int, default=10, help="rollout 수 (성공률 분모)")
    p.add_argument("--max-frames", type=int, default=100, help="rollout 당 정책 스텝 수 (chunk_size=100)")
    p.add_argument("--video-rollouts", type=int, default=3, help="영상으로 저장할 rollout 수")
    p.add_argument("--device", choices=["cpu", "mps", "cuda"], default="cpu",
                   help="추론 device (기본 cpu — 학습 MPS와 경합 회피)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--dr", action="store_true",
                   help="Domain Randomization 적용 후 측정 (조명/마찰/카메라노이즈). "
                        "결과는 rollout_summary_dr.json 로 별도 저장 — 운영 summary 불변.")
    p.add_argument("--dr-axes", type=str, default="light,friction,camera",
                   help="DR 무작위화 축 부분집합 (쉼표구분: light,friction,camera). "
                        "부분집합이면 rollout_summary_dr_<axes>.json 로 저장 — 3축 aggregate/운영 summary 불변.")
    p.add_argument("--summary-suffix", type=str, default="",
                   help="summary 파일명 접미사 (예: _seed7) — 수동 비교 측정이 운영 파일을 덮어쓰지 않게.")
    args = p.parse_args(argv)

    import torch
    import mujoco
    import imageio.v2 as imageio

    ckpt = Path(args.checkpoint) if args.checkpoint else find_latest_checkpoint()
    if ckpt is None or not ckpt.exists():
        print(json.dumps({"status": "error", "message": f"체크포인트 없음: {ckpt}"}, ensure_ascii=False))
        sys.exit(1)
    ckpt = ckpt.resolve()  # 상대경로(--checkpoint)도 ROOT 기준 절대경로로 — relative_to 안전

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # train_act.build_model 재사용 — config 를 명시 전달해 ACTPolicy.from_pretrained 의
    # config.json draccus 파싱(Python 3.14 에서 `Dict|None` 비호환)을 회피. 학습과 동일한 모델 구성 보장.
    sys.path.insert(0, str(ROOT / "scripts"))
    import train_act as T
    cfg = T.ACTTrainingConfig()
    policy = T.build_model(cfg, resume_from=str(ckpt), device=args.device)
    if policy is None:
        print(json.dumps({"status": "error", "message": "build_model 실패 (torch/lerobot 확인)"}, ensure_ascii=False))
        sys.exit(1)
    policy.eval()
    device = T._device_of(policy)

    model = mujoco.MjModel.from_xml_path(str(MODEL_XML))
    for ai in range(5):              # 팔 5관절 forcerange = 수집과 동일 (12V faithful)
        model.actuator_forcerange[ai] = [-ARM_FORCERANGE, ARM_FORCERANGE]
    data = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=480, width=640)
    cam_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, "overhead_camera")
    if cam_id < 0:
        cam_id = -1

    # DR 모듈 로드 (opt-in). samples/training 을 path 에 추가.
    dr_mod = dr_baseline = dr_rng = dr_axes = None
    if args.dr:
        sys.path.insert(0, str(ROOT / "samples" / "training"))
        import sim_domain_randomization as dr_mod
        dr_baseline = dr_mod.snapshot_baseline(model)
        dr_rng = np.random.default_rng(args.seed)
        dr_axes = tuple(a.strip() for a in args.dr_axes.split(",") if a.strip())
        valid = set(dr_mod.DR_AXES)
        bad = [a for a in dr_axes if a not in valid]
        if bad:
            print(json.dumps({"status": "error", "message": f"알 수 없는 DR 축: {bad} (허용: {sorted(valid)})"},
                             ensure_ascii=False))
            sys.exit(1)

    rng = np.random.default_rng(args.seed)
    t0 = time.time()
    results = []
    video_frames = []
    trajectories = []
    for i in range(args.rollouts):
        collect = i < args.video_rollouts
        try:
            success, max_lift, frames, traj = run_rollout(
                model, data, policy, renderer, cam_id, device, rng, args.max_frames, collect,
                dr_mod=dr_mod, dr_baseline=dr_baseline, dr_rng=dr_rng, dr_axes=dr_axes
            )
        except Exception as e:  # 한 rollout 실패가 전체 측정을 죽이지 않게
            results.append({"rollout": i, "success": False, "max_lift_m": 0.0, "error": str(e)[:120]})
            print(f"  rollout {i+1}/{args.rollouts}: ⚠ 에러 {str(e)[:80]}", flush=True)
            continue
        results.append({"rollout": i, "success": success, "max_lift_m": round(max_lift, 4)})
        trajectories.append({"rollout": i, "success": success,
                             "max_lift_m": round(max_lift, 4), "frames": traj})
        if collect:
            video_frames.extend(frames)
        print(f"  rollout {i+1}/{args.rollouts}: {'성공' if success else '실패'} (max_lift={max_lift*1000:.1f}mm)",
              flush=True)

    renderer.close()

    n_success = sum(r["success"] for r in results)
    success_rate = n_success / len(results) if results else 0.0

    # 영상 저장 — ckpt 디렉터리/DR/seed 태그 포함 (같은 날 nominal·DR 측정이 서로 덮어쓰지 않게)
    epoch_tag = ckpt.name.replace("epoch_", "")
    date_tag = time.strftime("%Y%m%d")
    run_tag = ckpt.parent.name  # act / act_cl_dr ...
    dr_tag = ("_dr" + ("" if set(dr_axes) == set(dr_mod.DR_AXES) else "_" + "_".join(sorted(dr_axes)))) if args.dr else ""
    seed_tag = f"_seed{args.seed}" if args.seed != 42 else ""
    video_path = OUT_DIR / f"inference_{run_tag}_epoch_{epoch_tag}_{date_tag}{dr_tag}{seed_tag}.mp4"
    if video_frames:
        imageio.mimsave(str(video_path), video_frames, fps=SIM_FPS)

    lifts_mm = sorted(r["max_lift_m"] * 1000 for r in results)
    median_lift = lifts_mm[len(lifts_mm) // 2] if lifts_mm else 0.0
    summary = {
        "status": "ok",
        "checkpoint": str(ckpt.relative_to(ROOT)),
        "ckpt_dir": run_tag,
        "scene": MODEL_XML.name,
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "seed": args.seed,
        "rollouts": len(results),
        "success": n_success,
        "success_rate": round(success_rate, 3),
        "median_lift_mm": round(median_lift, 1),
        "lift_threshold_m": LIFT_THRESHOLD_M,
        "dr": args.dr,
        "dr_axes": list(dr_axes) if dr_axes else None,
        "video_path": str(video_path.relative_to(ROOT)) if video_frames else None,
        "wall_clock_sec": round(time.time() - t0, 1),
        "device": args.device,
        "results": results,
    }
    # 요약 json (대시보드/크론이 성공률 읽기용). DR-on 은 별도 파일 — 운영 summary 불변.
    # 3축 전부 = aggregate(rollout_summary_dr.json). 부분집합 = ablation 별도 파일.
    if not args.dr:
        summary_name = f"rollout_summary{args.summary_suffix}.json"
    elif set(dr_axes) == set(dr_mod.DR_AXES):
        summary_name = f"rollout_summary_dr{args.summary_suffix}.json"
    else:
        summary_name = f"rollout_summary_dr_{'_'.join(sorted(dr_axes))}{args.summary_suffix}.json"
    (OUT_DIR / summary_name).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 불변 히스토리 사본 + 3D 리플레이 궤적 — 측정할 때마다 축적 (사이트 성과 차트/리플레이 데이터원).
    # 운영 summary 는 '최신' 슬롯으로 덮어써도 히스토리는 영구 보존된다.
    hist_dir = OUT_DIR / "history"
    hist_dir.mkdir(exist_ok=True)
    hist_stamp = time.strftime("%Y%m%d-%H%M%S")
    hist_base = f"{hist_stamp}_{run_tag}_{ckpt.name}{dr_tag}{seed_tag}"
    (hist_dir / f"{hist_base}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    traj_payload = {
        "checkpoint": str(ckpt.relative_to(ROOT)),
        "scene": MODEL_XML.name,
        "ckpt_dir": run_tag,
        "measured_at": summary["measured_at"],
        "seed": args.seed,
        "dr": args.dr,
        "fps": round(1.0 / (0.002 * DATA_SAMPLE_EVERY), 2),  # 궤적 1프레임 = 정책 1스텝 = 물리 17스텝×2ms ≈ 29.4fps
        "joint_names": ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"],
        "frame_format": "qpos[0:6] + cube_xyz[6:9]",
        "rollouts": trajectories,
    }
    (hist_dir / f"{hist_base}_traj.json").write_text(
        json.dumps(traj_payload, ensure_ascii=False), encoding="utf-8"
    )
    if not args.dr and not args.summary_suffix:
        # 운영(nominal) 측정의 최신 궤적 — 대시보드 3D 리플레이가 이 고정 경로를 읽는다
        (OUT_DIR / "rollout_traj_latest.json").write_text(
            json.dumps(traj_payload, ensure_ascii=False), encoding="utf-8"
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # 크론 측정 스테이지가 절대 안 죽게 — 에러도 JSON 으로 emit
        print(json.dumps(
            {"status": "error", "stage": "rollout_top_level", "message": str(e)[:200]},
            ensure_ascii=False,
        ))
        sys.exit(1)
