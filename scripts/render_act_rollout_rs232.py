#!/Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv/bin/python
"""RS232 케이블 분리(3단계, Phase 4) ACT 정책 rollout 측정 — render_act_rollout_s1.py 의 RS232 판본.

S1 측정기와 같은 규약, 다른 점만:
  - 씬/물리 = sim_rs232_unplug.Rs232UnplugTwin 그대로 (DE-9 치수·보유력·존 = 트윈 상수, 측정용으로 안 바꿈).
  - 관측 2카메라 observation.images.{top,closeup}, 상하반전 없음 (RS232 수집기도 raw 렌더 저장).
  - 판정 = 플러그 슬라이드 변위 latch 2종 (트윈 UNPLUG_* 상수 import, 수집기와 공유):
      partial = 변위 ≥ UNPLUG_PARTIAL_M (결합 깊이 절반, 2.95mm)
      full    = 변위 ≥ UNPLUG_FULL_M    (D 쉘 결합 깊이, 5.90mm = 완전 분리)
    success / success_rate = **부분성공(partial)** — 로드맵 Phase 4 완료 기준 '시뮬 분리 부분성공 50%'
    와 드라이버 TARGET_RATE(0.50) 가 같은 단위가 되도록. 완전분리는 full_success / full_rate 로 항상 병기.
  - 물리 스텝은 twin.step() — latch 가 그 안에서 갱신.
  - DR 측정 모드 없음 (Phase 4 W2 'DR 강화' 때 S1 판본 --dr 을 이식).

알려진 측정 간극 (S1 과 동일): 학습 데이터는 h264 왕복 프레임, rollout 은 무손실 raw 렌더.

산출물 (S1 과 같은 규약, 기본 OUT_DIR = research/simulation/inference_progress):
  1) inference_act_rs232_sim_epoch_{NN}_{date}.mp4 (nominal seed 만)
  2) rollout_summary_rs232[_seedN].json
  3) history/{stamp}_act_rs232_sim_{ckpt}[_seedN].json + nominal 만 _traj.json

사용:
  .venv/bin/python3 scripts/render_act_rollout_rs232.py                  # 최신 ckpt, 4-seed×10, cpu
  .venv/bin/python3 scripts/render_act_rollout_rs232.py --seeds 42 --rollouts 1 \
      --checkpoint checkpoints/act_s1_sim/epoch_0029 --out-dir /tmp/x     # 코드경로 스모크 (운영 요약 불변)
"""

import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path("/Volumes/MARK_DATA/dev/2026-cop-physical-ai")
OUT_DIR = ROOT / "research" / "simulation" / "inference_progress"

# 학습 샘플링과 동일 — RS232 수집기는 S1 PressExpert._phys_step 을 상속 (DATA_SAMPLE_EVERY=17).
DATA_SAMPLE_EVERY = 17
N_JOINTS = 6
SIM_FPS = 30
# expert 시연 길이: 고정 단계 1920 물리스텝 + 당김 150×k(k≤10) → 113+9k 프레임, 스모크 실측 158(k=5), 최대 ~201.
# 최대 시연 길이 + ~20% 여유 (S1: 최대 106 → 120 과 같은 방식).
DEFAULT_MAX_FRAMES = 240
DEFAULT_SEEDS = "42,7,123,2026"

RUN_TAG = "act_rs232_sim"


def find_latest_checkpoint() -> Path | None:
    ckpt_dir = Path(os.environ.get("COP_CKPT_DIR", str(ROOT / "checkpoints" / RUN_TAG)))
    ckpts = sorted(
        ckpt_dir.glob("epoch_*/"),
        key=lambda p: (p / "model.safetensors").stat().st_mtime
        if (p / "model.safetensors").exists() else 0.0,
    )
    return ckpts[-1] if ckpts else None


def _rel(p: Path) -> str:
    """ROOT 상대경로 (--out-dir 가 ROOT 밖이면 절대경로)."""
    p = Path(p).resolve()
    return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)


def run_rollout(twin, policy, device, rng, max_frames, collect_frames):
    """단일 rollout. (partial, full, max_disp_m, partial_frame, full_frame, top_frames, traj, placement)."""
    import torch

    placement = twin.reset(rng)          # 홈 자세 + S1 존 무작위화(관통 배치 재추첨) + latch 해제
    policy.reset()
    frames, traj = [], []
    partial_frame = full_frame = None
    max_disp = 0.0

    for step in range(max_frames):
        top = twin.render("top")         # 반전 없음 (수집기와 동일)
        closeup = twin.render("closeup")
        if collect_frames:
            frames.append(top.copy())

        img_top = torch.from_numpy(top).permute(2, 0, 1).float().div_(255.0)
        img_cu = torch.from_numpy(closeup).permute(2, 0, 1).float().div_(255.0)
        state = torch.from_numpy(twin.data.qpos[:N_JOINTS].astype(np.float32))
        batch = {
            "observation.images.top": img_top.unsqueeze(0).to(device),
            "observation.images.closeup": img_cu.unsqueeze(0).to(device),
            "observation.state": state.unsqueeze(0).to(device),
        }
        with torch.no_grad():
            action = policy.select_action(batch)
        twin.data.ctrl[:N_JOINTS] = action.squeeze(0).cpu().numpy()

        for _ in range(DATA_SAMPLE_EVERY):
            twin.step()                  # partial/full latch 갱신

        max_disp = max(max_disp, twin.plug_displacement())
        if twin.unplugged_partial() and partial_frame is None:
            partial_frame = step
        if twin.unplugged_full() and full_frame is None:
            full_frame = step
        traj.append([round(float(q), 4) for q in twin.data.qpos[:N_JOINTS]])

    return (twin.unplugged_partial(), twin.unplugged_full(), max_disp,
            partial_frame, full_frame, frames, traj, placement)


def measure_seed(twin, policy, device, seed, rollouts, max_frames, video_rollouts):
    rng = np.random.default_rng(seed)
    results, trajectories, video_frames = [], [], []
    for i in range(rollouts):
        collect = i < video_rollouts
        try:
            part, full, disp, pf, ff, frames, traj, placement = run_rollout(
                twin, policy, device, rng, max_frames, collect)
        except Exception as e:  # 한 rollout 실패가 전체 측정을 죽이지 않게
            results.append({"rollout": i, "success": False, "full_success": False,
                            "max_disp_mm": 0.0, "error": str(e)[:120]})
            print(f"  seed{seed} rollout {i+1}/{rollouts}: ⚠ {str(e)[:80]}", flush=True)
            continue
        results.append({"rollout": i, "success": part, "full_success": full,
                        "max_disp_mm": round(disp * 1000, 2),
                        "partial_frame": pf, "full_frame": ff})
        trajectories.append({"rollout": i, "success": part, "full_success": full,
                             "max_disp_m": round(disp, 4), "partial_frame": pf, "full_frame": ff,
                             "pcb": placement, "frames": traj})
        if collect:
            video_frames.extend(frames)
        tag = "완전분리" if full else ("부분성공" if part else "실패")
        print(f"  seed{seed} rollout {i+1}/{rollouts}: {tag} (max 변위={disp*1000:.2f}mm)", flush=True)
    return results, trajectories, video_frames


def write_outputs(out_dir, ckpt, seed, is_nominal, results, trajectories, video_frames,
                  max_frames, wall_sec, device, partial_mm, full_mm, timestep):
    n = len(results)
    n_part = sum(r["success"] for r in results)
    n_full = sum(r["full_success"] for r in results)
    median_disp = statistics.median(r["max_disp_mm"] for r in results) if results else 0.0
    date_tag = time.strftime("%Y%m%d")
    seed_tag = "" if is_nominal else f"_seed{seed}"

    video_path = None
    if video_frames:  # 영상은 nominal(seed42)만
        import imageio.v2 as imageio
        vp = out_dir / f"inference_{RUN_TAG}_epoch_{ckpt.name.replace('epoch_', '')}_{date_tag}{seed_tag}.mp4"
        imageio.mimsave(str(vp), video_frames, fps=SIM_FPS)
        video_path = _rel(vp)

    summary = {
        "status": "ok",
        "task": "rs232_unplug",
        "metric": "plug_partial_latch",          # success/success_rate = 부분성공, full_* = 완전분리
        "checkpoint": _rel(ckpt),
        "ckpt_dir": RUN_TAG,
        "scene": "rs232_unplug_scene.xml",
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "seed": seed,
        "rollouts": n,
        "success": n_part,
        "success_rate": round(n_part / n, 3) if n else 0.0,
        "full_success": n_full,
        "full_rate": round(n_full / n, 3) if n else 0.0,
        "median_disp_mm": round(median_disp, 2),
        "median_lift_mm": round(median_disp, 2),  # 대시보드 비교표 컬럼 호환 (RS232=최대 플러그 변위)
        "partial_threshold_mm": round(partial_mm, 2),   # 트윈 UNPLUG_PARTIAL_M 에서 파생
        "full_threshold_mm": round(full_mm, 2),         # 트윈 UNPLUG_FULL_M 에서 파생
        "max_frames": max_frames,
        "dr": False,
        "dr_axes": None,
        "video_path": video_path,
        "wall_clock_sec": round(wall_sec, 1),
        "device": device,
        "results": results,
    }
    (out_dir / f"rollout_summary_rs232{seed_tag}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    hist_dir = out_dir / "history"
    hist_dir.mkdir(exist_ok=True)
    hist_base = f"{time.strftime('%Y%m%d-%H%M%S')}_{RUN_TAG}_{ckpt.name}{seed_tag}"
    (hist_dir / f"{hist_base}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if not is_nominal:  # 궤적은 nominal 만 (리플레이 = 영상 seed 일치)
        return summary
    traj_payload = {
        "checkpoint": _rel(ckpt),
        "scene": "rs232_unplug_scene.xml",
        "ckpt_dir": RUN_TAG,
        "measured_at": summary["measured_at"],
        "seed": seed,
        "dr": False,
        "fps": round(1.0 / (timestep * DATA_SAMPLE_EVERY), 2),
        "joint_names": ["shoulder_pan", "shoulder_lift", "elbow_flex",
                        "wrist_flex", "wrist_roll", "gripper"],
        "frame_format": "qpos[0:6]",  # 플러그 판정은 rollout.{partial,full}_frame / max_disp_m, PCB 배치는 rollout.pcb
        "rollouts": trajectories,
    }
    (hist_dir / f"{hist_base}_traj.json").write_text(
        json.dumps(traj_payload, ensure_ascii=False), encoding="utf-8")
    return summary


def main(argv=None):
    p = argparse.ArgumentParser(description="RS232 케이블 분리 ACT rollout 측정 (플러그 변위 latch 4-seed)")
    p.add_argument("--checkpoint", type=str, default=None, help="ckpt 디렉터리 (기본: 최신)")
    p.add_argument("--rollouts", type=int, default=10, help="seed 당 rollout 수")
    p.add_argument("--max-frames", type=int, default=DEFAULT_MAX_FRAMES)
    p.add_argument("--video-rollouts", type=int, default=3, help="영상 저장 rollout 수 (nominal seed)")
    p.add_argument("--seeds", type=str, default=DEFAULT_SEEDS, help="쉼표구분 seed 목록 (첫 seed=nominal)")
    p.add_argument("--device", choices=["cpu", "mps", "cuda"], default="cpu")
    p.add_argument("--out-dir", type=str, default=str(OUT_DIR),
                   help="산출물 디렉터리 (스모크용 — 기본은 운영 inference_progress)")
    args = p.parse_args(argv)

    ckpt = Path(args.checkpoint) if args.checkpoint else find_latest_checkpoint()
    if ckpt is None or not ckpt.exists():
        print(json.dumps({"status": "error", "message": f"체크포인트 없음: {ckpt}"}, ensure_ascii=False))
        sys.exit(1)
    ckpt = ckpt.resolve()
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    if not seeds:
        print(json.dumps({"status": "error", "message": f"유효한 seed 없음: --seeds={args.seeds!r}"},
                         ensure_ascii=False))
        sys.exit(1)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(ROOT / "scripts"))
    import train_act as T
    cfg = T.ACTTrainingConfig()
    cfg.camera_keys = ["top", "closeup"]      # RS232 데이터셋 2카메라 계약 (env 무관)
    policy = T.build_model(cfg, resume_from=str(ckpt), device=args.device)
    if policy is None:
        print(json.dumps({"status": "error", "message": "build_model 실패 (torch/lerobot 확인)"},
                         ensure_ascii=False))
        sys.exit(1)
    policy.eval()
    device = T._device_of(policy)

    sys.path.insert(0, str(ROOT / "samples" / "training"))
    from sim_rs232_unplug import Rs232UnplugTwin, UNPLUG_PARTIAL_M, UNPLUG_FULL_M
    twin = Rs232UnplugTwin()
    timestep = float(twin.model.opt.timestep)

    summaries = []
    for si, seed in enumerate(seeds):
        is_nominal = si == 0
        t0 = time.time()
        results, trajectories, video_frames = measure_seed(
            twin, policy, device, seed, args.rollouts, args.max_frames,
            args.video_rollouts if is_nominal else 0)
        s = write_outputs(out_dir, ckpt, seed, is_nominal, results, trajectories, video_frames,
                          args.max_frames, time.time() - t0, str(device),
                          UNPLUG_PARTIAL_M * 1000, UNPLUG_FULL_M * 1000, timestep)
        summaries.append(s)
        print(f"seed{seed}: 부분성공 {s['success_rate']} ({s['success']}/{s['rollouts']}) · "
              f"완전분리 {s['full_rate']} ({s['full_success']}/{s['rollouts']}) · {s['wall_clock_sec']}s", flush=True)

    twin.close()
    mean = lambda xs: round(sum(xs) / len(xs), 3)
    part = [s["success_rate"] for s in summaries]
    full = [s["full_rate"] for s in summaries]
    print(json.dumps({
        "status": "ok", "checkpoint": _rel(ckpt),
        "seeds": seeds, "per_seed": part, "per_seed_full": full,
        "fair_estimate": mean(part), "full_fair_estimate": mean(full),
        "success_rate": mean(part),  # 드라이버 stage6 grep 호환 (= 부분성공 4-seed 공정추정, TARGET_RATE 0.50 과 같은 단위)
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # 크론 측정 스테이지가 절대 안 죽게 — 에러도 JSON emit
        print(json.dumps(
            {"status": "error", "stage": "rollout_rs232_top_level", "message": str(e)[:200]},
            ensure_ascii=False))
        sys.exit(1)
