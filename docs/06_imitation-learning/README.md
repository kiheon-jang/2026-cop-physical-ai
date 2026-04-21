# 모방학습 가이드 (Step 06)

> ACT(Action Chunking Transformer) 또는 Diffusion Policy로 수집된 데이터를 학습합니다.

## 지원 정책(Policy) 종류

| Policy | 특징 | 권장 사용 |
|--------|------|-----------|
| **ACT** | 빠른 학습, 낮은 연산 비용 | 첫 학습 시 권장 |
| **Diffusion Policy** | 높은 성능, 연산 비용 큼 | 성능 개선 시 |
| **π0 (pi0)** | 최신 VLA 기반 | 고급 단계 |

## ACT 학습

```bash
# 기본 ACT 학습
python lerobot/scripts/train.py \
  --policy.type=act \
  --dataset.repo_id=kiheon-jang/hdel_iot_pick_place_v1 \
  --env.type=so101 \
  --output_dir=outputs/train/act_pick_place_v1 \
  --training.num_epochs=100 \
  --training.batch_size=8 \
  --device=cuda  # Jetson Orin: cuda, Mac: mps, CPU: cpu
```

## Diffusion Policy 학습

```bash
python lerobot/scripts/train.py \
  --policy.type=diffusion \
  --dataset.repo_id=kiheon-jang/hdel_iot_pick_place_v1 \
  --output_dir=outputs/train/diffusion_pick_place_v1 \
  --training.num_epochs=200 \
  --training.batch_size=4
```

## 학습 모니터링 (WandB)

```bash
# WandB 연동
wandb login
python lerobot/scripts/train.py \
  --policy.type=act \
  --dataset.repo_id=kiheon-jang/hdel_iot_pick_place_v1 \
  --wandb.enable=true \
  --wandb.project=cop-physical-ai
```

## 인퍼런스 (실물 로봇 테스트)

```bash
python lerobot/scripts/control_robot.py \
  --robot.type=so101_follower \
  --robot.port=/dev/tty.usbmodem5AE60573201 \
  --robot.id=hdel_iot_01_follower_arm \
  --policy.path=outputs/train/act_pick_place_v1/checkpoints/last \
  --robot.cameras.top='{"type":"opencv","index_or_path":0,"width":640,"height":480,"fps":30}' \
  --robot.cameras.gripper='{"type":"opencv","index_or_path":2,"width":640,"height":480,"fps":30}'
```

## 성능 평가 기준
- **목표**: 실물 성공률 80% 이상
- **평가 방법**: 10회 시도 중 성공 횟수
- **실패 분석**: 카메라 영상 + 모터 토크 데이터 기록

## 참고
- [LeRobot Training 공식 문서](https://huggingface.co/docs/lerobot/training)
- [ACT 논문](https://arxiv.org/abs/2304.13705)
- [Diffusion Policy 논문](https://diffusion-policy.cs.columbia.edu/)
