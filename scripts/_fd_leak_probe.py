"""FD 누수 진단 프로브 (2026-07-15). 학습 재실행 아님 — num_workers=0 DataLoader 를
mini-epoch(5 step) 로 여러 번 재순회하며 열린 FD 수 증가를 측정. 원천 규명용."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from train_act import ACTTrainingConfig, load_dataset

def open_fds():
    try:
        return len(os.listdir("/dev/fd"))
    except OSError:
        return -1

cfg = ACTTrainingConfig()
cfg.dataset_root = "data/episodes_floor"
dl = load_dataset(cfg, num_workers=0)
if dl is None:
    print("BLOCKED: lerobot/torch 미가용"); sys.exit(1)

print(f"baseline fds after load: {open_fds()}", flush=True)
for ep in range(4):
    n = 0
    for step, batch in enumerate(dl):   # full exhaustion (drop_last StopIteration)
        n += 1
    print(f"full-epoch {ep}: steps={n} open_fds={open_fds()}", flush=True)
