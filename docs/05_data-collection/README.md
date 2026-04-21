# 데이터 수집 가이드 (Step 05)

> **현재 단계** — 텔레오퍼레이션으로 학습용 에피소드 데이터를 수집합니다.

## 목표
- 최소 50개 이상의 에피소드 수집
- 태스크: 물체 이동 (Pick & Place)
- 카메라: Top mount + Gripper (2채널)

## 데이터 수집 명령어

```bash
# 데이터셋 이름 설정 (HuggingFace Hub 업로드용)
DATASET_REPO_ID="kiheon-jang/hdel_iot_pick_place_v1"

lerobot-record \
  --robot.type=so101_follower \
  --robot.port=/dev/tty.usbmodem5AE60573201 \
  --robot.id=hdel_iot_01_follower_arm \
  --teleop.type=so101_leader \
  --teleop.port=/dev/tty.usbmodem5AE60537131 \
  --teleop.id=hdel_iot_01_leader_arm \
  --dataset.repo_id=${DATASET_REPO_ID} \
  --dataset.num_episodes=50 \
  --dataset.fps=30
```

## 카메라 포함 수집

```bash
lerobot-record \
  --robot.type=so101_follower \
  --robot.port=/dev/tty.usbmodem5AE60573201 \
  --robot.id=hdel_iot_01_follower_arm \
  --teleop.type=so101_leader \
  --teleop.port=/dev/tty.usbmodem5AE60537131 \
  --teleop.id=hdel_iot_01_leader_arm \
  --robot.cameras.top='{"type":"opencv","index_or_path":0,"width":640,"height":480,"fps":30}' \
  --robot.cameras.gripper='{"type":"opencv","index_or_path":2,"width":640,"height":480,"fps":30}' \
  --dataset.repo_id=${DATASET_REPO_ID} \
  --dataset.num_episodes=50
```

## 수집 팁
- 에피소드당 5~10초 내외의 단순 동작 권장
- 실패한 에피소드는 즉시 재수집 (키보드 단축키: `d` = discard)
- 조명 일정하게 유지
- 매 세션 시작 전 캘리브레이션 확인

## 데이터 확인

```bash
# 수집된 데이터셋 시각화
lerobot-visualize-dataset \
  --repo-id ${DATASET_REPO_ID} \
  --episode-index 0
```

## 참고
- [LeRobot 데이터 수집 공식 문서](https://huggingface.co/docs/lerobot/record)
