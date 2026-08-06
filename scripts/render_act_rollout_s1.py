#!/Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv/bin/python
"""S1 리셋버튼 ACT 정책 rollout 측정 (실기 정렬) — render_act_rollout.py 의 S1 판본.

pick-place rollout 과 다른 점 (전부 학습 데이터 계약에서 나온다):
  - 씬/물리 = sim_pcb_reset.PcbResetTwin 그대로 재사용 (버튼 치수·스프링·존 = 실기 기준,
    성공률을 위해 바꾸지 않음 — 환경 불변 원칙 2026-08-05).
  - 관측 2카메라 observation.images.{top,closeup}, **상하반전 없음**
    (S1 수집기 sim_pcb_reset.render 는 raw 렌더 저장 — pick-place 수집기의 [::-1] 와 다르다).
  - 성공 판정 = **LED latch** (버튼 슬라이드 조인트 변위 임계 → 한 번 눌리면 점등 유지).
    실기 P1 녹색 LED 판정과 동일 계약. 시뮬은 정답이 공짜.
  - 물리 스텝은 twin.step() 으로 — LED latch 가 그 안에서 갱신된다.

알려진 측정 간극 (pick-place render_act_rollout.py 와 동일 방법론):
  학습 데이터셋은 h264 영상으로 저장(수집기 use_videos=True)돼 백본이 본 프레임은
  인코드→디코드(YUV420 손실)를 거쳤지만, 여기 rollout 은 무손실 raw 렌더를 그대로 먹인다.
  resnet18 기준 영향은 작지만 0 은 아니다(정책이 '너무 깨끗한' 입력을 봄). 프레임별 h264
  왕복은 비용 대비 실익이 없어 채택하지 않고 이 간극을 명시만 한다.

산출물 (대시보드/3D 리플레이가 glob 으로 자동 소비):
  1) rollout 영상 → inference_progress/inference_act_s1_sim_epoch_{NN}_{date}.mp4
     (build_inference_progress 가 스캔, run=act_s1_sim → track 2)
  2) rollout_summary_s1[_seedN].json  (성공률 = LED latch 비율)
  3) history/{stamp}_act_s1_sim_...json + _traj.json  (성과 차트 + 3D 리플레이)

4-seed 프로토콜: seeds 42,7,123,2026 을 한 실행에서 전부 측정. seed42 = 운영(nominal)
슬롯 rollout_summary_s1.json, 나머지는 _seedN. 영상은 nominal(seed42)만.

사용:
  .venv/bin/python3 scripts/render_act_rollout_s1.py                 # 최신 ckpt, 4-seed×10, cpu
  .venv/bin/python3 scripts/render_act_rollout_s1.py --device mps    # 학습 종료 후엔 mps 가 빠름
  .venv/bin/python3 scripts/render_act_rollout_s1.py --seeds 42 --rollouts 3   # 스모크
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

# 학습 샘플링과 동일해야 한다 — 정책 1액션당 물리 17스텝 (sim_pcb_reset_collector.DATA_SAMPLE_EVERY).
DATA_SAMPLE_EVERY = 17
N_JOINTS = 6
SIM_FPS = 30
# 데모 에피소드 길이 66~106 프레임(mean 72) → 120 프레임이면 press 완주 여유.
DEFAULT_MAX_FRAMES = 120
DEFAULT_SEEDS = "42,7,123,2026"

RUN_TAG = "act_s1_sim"  # sim3dModelLabel / build_inference_progress track 판별 키


def find_latest_checkpoint() -> Path | None:
    ckpt_dir = Path(os.environ.get("COP_CKPT_DIR", str(ROOT / "checkpoints" / RUN_TAG)))
    ckpts = sorted(
        ckpt_dir.glob("epoch_*/"),
        key=lambda p: (p / "model.safetensors").stat().st_mtime
        if (p / "model.safetensors").exists() else 0.0,
    )
    return ckpts[-1] if ckpts else None


def run_rollout(twin, policy, device, rng, max_frames, collect_frames):
    """단일 S1 rollout. (success, press_depth_m, led_frame, top_frames, traj, placement) 반환."""
    import torch

    placement = twin.reset(rng)          # 홈 자세 + 15×15cm 존 무작위화 + LED off
    policy.reset()                       # ACT 액션 큐 초기화
    frames = []                          # 영상용 top 카메라 프레임
    traj = []                            # 3D 리플레이용 qpos6 (프레임당)
    led_frame = None
    min_btn = 0.0                        # 버튼 최저 변위 (음수) → press 깊이

    for step in range(max_frames):
        top = twin.render("top")         # (480,640,3) uint8 — **반전 없음** (수집기와 동일)
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
            action = policy.select_action(batch)      # (1,6) 비정규화 ctrl 타겟
        twin.data.ctrl[:N_JOINTS] = action.squeeze(0).cpu().numpy()

        for _ in range(DATA_SAMPLE_EVERY):
            twin.step()                  # LED latch 가 여기서 갱신됨

        btn = float(twin.data.qpos[twin._btn_qadr])
        min_btn = min(min_btn, btn)
        if twin.led_on() and led_frame is None:
            led_frame = step
        traj.append([round(float(q), 4) for q in twin.data.qpos[:N_JOINTS]])

    return twin.led_on(), -min_btn, led_frame, frames, traj, placement


def measure_seed(twin, policy, device, seed, rollouts, max_frames, video_rollouts):
    """한 seed 의 rollout 묶음. (results, trajectories, video_frames, placements) 반환."""
    rng = np.random.default_rng(seed)
    results, trajectories, video_frames = [], [], []
    for i in range(rollouts):
        collect = i < video_rollouts
        try:
            ok, depth_m, led_f, frames, traj, placement = run_rollout(
                twin, policy, device, rng, max_frames, collect)
        except Exception as e:  # 한 rollout 실패가 전체 측정을 죽이지 않게
            results.append({"rollout": i, "success": False, "press_depth_mm": 0.0,
                            "error": str(e)[:120]})
            print(f"  seed{seed} rollout {i+1}/{rollouts}: ⚠ {str(e)[:80]}", flush=True)
            continue
        results.append({"rollout": i, "success": ok,
                        "press_depth_mm": round(depth_m * 1000, 2), "led_frame": led_f})
        trajectories.append({"rollout": i, "success": ok, "press_depth_m": round(depth_m, 4),
                             "led_frame": led_f, "pcb": placement, "frames": traj})
        if collect:
            video_frames.extend(frames)
        print(f"  seed{seed} rollout {i+1}/{rollouts}: "
              f"{'성공(LED)' if ok else '실패'} (press={depth_m*1000:.1f}mm)", flush=True)
    return results, trajectories, video_frames


def write_outputs(ckpt, seed, is_nominal, results, trajectories, video_frames,
                  max_frames, wall_sec, device, press_threshold_mm, timestep):
    n_success = sum(r["success"] for r in results)
    rate = n_success / len(results) if results else 0.0
    median_press = statistics.median(r["press_depth_mm"] for r in results) if results else 0.0
    date_tag = time.strftime("%Y%m%d")
    seed_tag = "" if is_nominal else f"_seed{seed}"

    video_path = None
    if video_frames:  # 영상은 nominal(seed42)만 — _seedN 영상은 대시보드가 어차피 스킵.
        # imageio import 는 여기서 — 측정 요약 JSON emit 이 영상 라이브러리에 볼모잡히지 않게.
        import imageio.v2 as imageio
        vp = OUT_DIR / f"inference_{RUN_TAG}_epoch_{ckpt.name.replace('epoch_', '')}_{date_tag}{seed_tag}.mp4"
        imageio.mimsave(str(vp), video_frames, fps=SIM_FPS)
        video_path = str(vp.relative_to(ROOT))

    summary = {
        "status": "ok",
        "task": "s1_reset_button",
        "metric": "led_latch",
        "checkpoint": str(ckpt.relative_to(ROOT)),
        "ckpt_dir": RUN_TAG,
        "scene": "pcb_reset_scene.xml",
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "seed": seed,
        "rollouts": len(results),
        "success": n_success,
        "success_rate": round(rate, 3),
        "median_press_mm": round(median_press, 2),
        "median_lift_mm": round(median_press, 2),  # 대시보드 비교표 컬럼 호환 (S1=press 깊이)
        "press_threshold_mm": round(press_threshold_mm, 2),  # 트윈 PRESS_THRESHOLD 에서 파생 (하드코딩 아님)
        "max_frames": max_frames,
        "dr": False,
        "video_path": video_path,
        "wall_clock_sec": round(wall_sec, 1),
        "device": device,  # 실제 해석된 device (요청값 아님)
        "results": results,
    }
    summary_name = f"rollout_summary_s1{seed_tag}.json"
    (OUT_DIR / summary_name).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    # 불변 히스토리 요약 (측정마다 축적 — 성과 차트 데이터원, seed 전부)
    hist_dir = OUT_DIR / "history"
    hist_dir.mkdir(exist_ok=True)
    hist_base = f"{time.strftime('%Y%m%d-%H%M%S')}_{RUN_TAG}_{ckpt.name}{seed_tag}"
    (hist_dir / f"{hist_base}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    # 3D 리플레이 궤적은 nominal(seed42)만 — build_web3d 가 (ckpt,checkpoint,날짜)로 dedupe 해
    # 어차피 1건만 살아남는다. nominal 만 남기면 리플레이=영상 seed 일치 + history/ 비대화 방지.
    if not is_nominal:
        return summary
    traj_payload = {
        "checkpoint": str(ckpt.relative_to(ROOT)),
        "scene": "pcb_reset_scene.xml",
        "ckpt_dir": RUN_TAG,
        "measured_at": summary["measured_at"],
        "seed": seed,
        "dr": False,
        "fps": round(1.0 / (timestep * DATA_SAMPLE_EVERY), 2),  # 씬 timestep 에서 파생
        "joint_names": ["shoulder_pan", "shoulder_lift", "elbow_flex",
                        "wrist_flex", "wrist_roll", "gripper"],
        "frame_format": "qpos[0:6]",  # S1: 큐브 없음 — PCB 배치는 rollout.pcb, LED 는 rollout.led_frame
        "rollouts": trajectories,
    }
    (hist_dir / f"{hist_base}_traj.json").write_text(
        json.dumps(traj_payload, ensure_ascii=False), encoding="utf-8")
    return summary


def main(argv=None):
    p = argparse.ArgumentParser(description="S1 리셋버튼 ACT rollout 측정 (LED latch 4-seed)")
    p.add_argument("--checkpoint", type=str, default=None, help="ckpt 디렉터리 (기본: 최신)")
    p.add_argument("--rollouts", type=int, default=10, help="seed 당 rollout 수")
    p.add_argument("--max-frames", type=int, default=DEFAULT_MAX_FRAMES)
    p.add_argument("--video-rollouts", type=int, default=3, help="영상 저장 rollout 수 (nominal seed)")
    p.add_argument("--seeds", type=str, default=DEFAULT_SEEDS, help="쉼표구분 seed 목록 (첫 seed=nominal)")
    p.add_argument("--device", choices=["cpu", "mps", "cuda"], default="cpu",
                   help="추론 device (기본 cpu; 학습 종료 후엔 mps 가 빠름)")
    args = p.parse_args(argv)

    import torch  # noqa: F401  (device 문자열 검증 및 build_model 내부에서 사용)

    ckpt = Path(args.checkpoint) if args.checkpoint else find_latest_checkpoint()
    if ckpt is None or not ckpt.exists():
        print(json.dumps({"status": "error", "message": f"체크포인트 없음: {ckpt}"}, ensure_ascii=False))
        sys.exit(1)
    ckpt = ckpt.resolve()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 정책 = 학습과 동일 구성으로 재구성 후 가중치 로드. 2카메라(top,closeup) 강제 —
    # env(COP_CAMERA_KEYS) 유무와 무관하게 S1 체크포인트(2카메라 백본)와 형상 일치.
    sys.path.insert(0, str(ROOT / "scripts"))
    import train_act as T
    cfg = T.ACTTrainingConfig()
    cfg.camera_keys = ["top", "closeup"]
    policy = T.build_model(cfg, resume_from=str(ckpt), device=args.device)
    if policy is None:
        print(json.dumps({"status": "error", "message": "build_model 실패 (torch/lerobot 확인)"},
                         ensure_ascii=False))
        sys.exit(1)
    policy.eval()
    device = T._device_of(policy)

    sys.path.insert(0, str(ROOT / "samples" / "training"))
    from sim_pcb_reset import PcbResetTwin, PRESS_THRESHOLD
    twin = PcbResetTwin()
    press_mm = abs(PRESS_THRESHOLD) * 1000        # 트윈 계약 상수에서 파생 (하드코딩 방지)
    timestep = float(twin.model.opt.timestep)

    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    if not seeds:  # 잘못된 --seeds 로 조용히 무작업 성공하지 않게 (크론 오설정 방어)
        print(json.dumps({"status": "error", "message": f"유효한 seed 없음: --seeds={args.seeds!r}"},
                         ensure_ascii=False))
        sys.exit(1)
    summaries = []
    for si, seed in enumerate(seeds):
        is_nominal = si == 0
        t0 = time.time()
        results, trajectories, video_frames = measure_seed(
            twin, policy, device, seed, args.rollouts, args.max_frames,
            args.video_rollouts if is_nominal else 0)  # 영상은 nominal seed 만
        summary = write_outputs(ckpt, seed, is_nominal, results, trajectories,
                                video_frames, args.max_frames, time.time() - t0,
                                str(device), press_mm, timestep)
        summaries.append(summary)
        print(f"seed{seed}: 성공률 {summary['success_rate']} "
              f"({summary['success']}/{summary['rollouts']}) · {summary['wall_clock_sec']}s", flush=True)

    twin.close()
    rates = [s["success_rate"] for s in summaries]
    fair = round(sum(rates) / len(rates), 3) if rates else None
    print(json.dumps({
        "status": "ok", "checkpoint": str(ckpt.relative_to(ROOT)),
        "seeds": seeds, "per_seed": rates, "fair_estimate": fair,
        "success_rate": fair,  # 크론 드라이버 stage6 grep 호환 (= 4-seed 공정추정)
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # 크론 측정 스테이지가 절대 안 죽게 — 에러도 JSON emit
        print(json.dumps(
            {"status": "error", "stage": "rollout_s1_top_level", "message": str(e)[:200]},
            ensure_ascii=False))
        sys.exit(1)
