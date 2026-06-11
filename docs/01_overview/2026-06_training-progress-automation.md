# 학습 진척 자동화 가이드 (PROG)

> 6/15 ACT 학습 시작 후 활성화할 자동화 — 메트릭 (loss curve) + 진척 영상 (inference)
> 이 자동으로 대시보드에 누적 노출되도록 하는 설정.

대시보드 노출 위치: 시뮬 영상 메뉴 → "학습 진척" 섹션 (학습 데이터셋 hero 바로 아래)

---

## 1. 학습 메트릭 자동 저장 — `train_act.py` 에 추가

### 저장 위치
```
outputs/train/<job_name>/metrics.jsonl
```

JSON Lines 포맷 (epoch 끝마다 1줄 append).

### `train()` 함수에 추가할 코드 스니펫

```python
import json
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
JOB_NAME = "act_pick_place_v1"  # 학습 잡명 (수정 가능)
METRICS_PATH = Path(f"outputs/train/{JOB_NAME}/metrics.jsonl")
METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)

def append_metric(epoch: int, step: int, loss: float, lr: float, val_loss: float | None = None):
    """매 epoch 끝에 호출. JSON Lines 한 줄 append."""
    record = {
        "epoch": epoch,
        "step": step,
        "loss": float(loss),
        "lr": float(lr),
        "timestamp": datetime.now(KST).isoformat(timespec="seconds"),
    }
    if val_loss is not None:
        record["val_loss"] = float(val_loss)
    with METRICS_PATH.open("a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
```

학습 루프 끝에서 호출:

```python
for epoch in range(num_epochs):
    train_loss = train_one_epoch(model, dataloader, optimizer)
    append_metric(epoch + 1, step, train_loss, optimizer.param_groups[0]["lr"])
```

→ `build.py` 의 `build_training_metrics()` 가 자동으로 읽어 대시보드 emit.

---

## 2. Inference 영상 자동 생성 — `cron 2 (23:30)` 페이로드에 추가

### 영상 저장 위치
```
research/simulation/inference_progress/inference_epoch_{NN}_{YYYY-MM-DD}.mp4
```

파일명에서 `epoch_NN` 추출되면 `build.py` 의 `build_inference_progress()` 가 자동 인식.

### `cron 2 (시뮬 테스트 + 메트릭 수집)` 페이로드 추가 블록

```text
## (추가) 학습 진척 Inference 영상 생성

1. 최신 체크포인트 확인:
   ls -t outputs/train/*/checkpoints/ 2>/dev/null | head -3
   체크포인트 없으면 이 단계 스킵.

2. 학습된 모델로 시뮬 환경에서 추론 5초 + mp4 저장:
   /Users/markmini/Documents/dev/2026-cop-physical-ai/.venv/bin/python3 \
     samples/inference/sim_inference_video.py \
     --checkpoint outputs/train/act_pick_place_v1/checkpoints/last \
     --output research/simulation/inference_progress/inference_epoch_$(현재 epoch)_$(date +%Y-%m-%d).mp4 \
     --duration 5

3. 영상 생성 성공 시 git add/commit:
   git add research/simulation/inference_progress/
   git commit -m "🎬 [학습] inference epoch $(epoch) — $(YYYY-MM-DD)"

4. 실패 시 자가치유 기록 (sandbox 권한 차단 등):
   agent/research-log/YYYY-MM-DD.md 에 추가
   [자가치유] inference 영상 생성 실패: <원인>. 다음 cron 재시도.
```

### `samples/inference/sim_inference_video.py` 신규 (가이드)

```python
"""학습된 ACT 모델로 시뮬 환경에서 추론 + 영상 저장."""
import argparse
import mujoco
import imageio
import torch
from lerobot.common.policies.act.modeling_act import ACTPolicy

parser = argparse.ArgumentParser()
parser.add_argument("--checkpoint", required=True)
parser.add_argument("--output", required=True)
parser.add_argument("--duration", type=float, default=5.0)
args = parser.parse_args()

# 1. 모델 로드
policy = ACTPolicy.from_pretrained(args.checkpoint)
policy.eval()

# 2. MuJoCo 시뮬 환경 초기화 (sim_pick_place.py 와 동일)
MODEL_PATH = "models/SO-ARM100/Simulation/SO101/so101_new_calib.xml"
model = mujoco.MjModel.from_xml_path(MODEL_PATH)
data = mujoco.MjData(model)
renderer = mujoco.Renderer(model, height=480, width=640)
mujoco.mj_resetData(model, data)

# 3. 추론 루프 — 매 step 마다 영상 + 모델 추론
fps = 30
n_frames = int(args.duration * fps)
frames = []
for step in range(n_frames):
    # 관측 추출
    renderer.update_scene(data, camera="top")
    img = renderer.render()  # (480, 640, 3)
    qpos = data.qpos[:6].copy()
    # 모델 추론
    with torch.no_grad():
        obs = {
            "observation.images.top": torch.tensor(img).permute(2, 0, 1).unsqueeze(0).float() / 255.0,
            "observation.state": torch.tensor(qpos).unsqueeze(0).float(),
        }
        action = policy.select_action(obs).cpu().numpy().squeeze()
    # 시뮬 1 step
    data.ctrl[:6] = action
    mujoco.mj_step(model, data)
    frames.append(img)

# 4. 영상 저장
imageio.mimsave(args.output, frames, fps=fps, codec="libx264")
print(f"✓ saved {args.output} ({n_frames} frames @ {fps} fps)")
```

---

## 3. 대시보드 자동 반영 흐름

```
1. cron 2 (23:30) → train_act.py 가 metrics.jsonl 에 epoch 추가
                  → sim_inference_video.py 가 mp4 1개 추가
                  → git add/commit/push
                  → 끝에서 build.py --json-only 호출

2. build.py
   → build_training_metrics() : metrics.jsonl 읽어 emit
   → build_inference_progress() : inference_progress/ 영상 list emit
   → data.json 갱신

3. hermes-mark
   → chokidar 가 data.json 변경 감지
   → WebSocket broadcast

4. 브라우저
   → renderTrainingProgress() 자동 호출
   → 학습 메트릭 카드 + loss curve SVG + inference 영상 grid 라이브 갱신
```

수동 새로고침 불필요. 매일 23:30 직후 새 영상/메트릭 1건씩 누적.

---

## 4. 활성화 체크리스트

학습 시작 (2026-06-15 또는 그 전) 직전에 수행:

- [ ] `train_act.py::train()` 에 `append_metric()` 코드 추가
- [ ] `samples/inference/sim_inference_video.py` 신규 작성 (위 가이드 참조)
- [ ] cron 2 페이로드 끝에 "(추가) 학습 진척 Inference 영상 생성" 블록 추가
- [ ] `.venv python3` 의 sandbox 권한 해제 (Hermes 측 — 23:30 cron 에서 .venv/bin/python3 실행 허용)
- [ ] 학습 시작 후 24h 후 대시보드 확인 — 학습 진척 섹션 자동 노출 확인

활성화 전까지는 대시보드에 **"학습 시작 대기 중 — 2026-06-15 시작 예정"** 안내 카드 자동 노출.
