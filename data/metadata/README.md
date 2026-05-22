# data/metadata/

에피소드 **메타데이터만** git 추적. 실제 에피소드 데이터(`data/episodes/`, `data/videos/`)는 `.gitignore`로 제외.

## 저장 전략

| Phase | 저장 방식 | 위치 |
|-------|---------|------|
| Phase 0 W4 (50 ep) | 로컬 전용 | `data/episodes/` (gitignore) |
| Phase 1+ (200+ ep) | HuggingFace private | `hf://kiheon-jang/cop-pickplace-v1` |

## Phase 1 업로드 명령 (예정)
```bash
# HuggingFace CLI 업로드 (Phase 1 W1 시작 시)
.venv/bin/python3 -c "
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
dataset = LeRobotDataset('local/cop-pickplace', root='data/episodes')
dataset.push_to_hub('kiheon-jang/cop-pickplace-v1', private=True)
"
```
