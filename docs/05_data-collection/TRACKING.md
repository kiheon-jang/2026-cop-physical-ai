# 📊 데이터 수집 현황 트래킹

> **목표: 50 에피소드** | 태스크: Pick & Place (물체 이동)  
> 팀원이 수집 후 직접 이 파일을 업데이트해주세요 (PR or 직접 커밋)

## 진행 현황

| 날짜 | 수집자 | 에피소드 수 | 누적 | 태스크 | 성공률 | 비고 |
|------|--------|-----------|------|--------|--------|------|
| - | - | 0 | 0 / 50 | Pick & Place | - | 시작 전 |

## 수집 체크리스트 (매 세션 전)
- [ ] Follower 캘리브레이션 확인
- [ ] Leader 캘리브레이션 확인
- [ ] Top 카메라 정상 작동 확인
- [ ] Gripper 카메라 정상 작동 확인
- [ ] 조명 일정하게 유지
- [ ] 물체 위치 초기화 (A 위치 고정)

## 수집 명령어
```bash
DATASET_REPO_ID="kiheon-jang/hdel_iot_pick_place_v1"

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

## 키보드 단축키 (수집 중)
| 키 | 동작 |
|----|------|
| `Enter` | 에피소드 저장 |
| `d` | 에피소드 버리기 (재수집) |
| `q` | 수집 종료 |

## 단계별 목표
- [ ] 10 에피소드 — 파이프라인 정상 확인
- [ ] 30 에피소드 — 중간 학습 테스트
- [ ] 50 에피소드 — ACT 학습 시작
- [ ] 100 에피소드 — Diffusion Policy 학습

## 품질 기준
- 에피소드당 권장 길이: **5~10초**
- 카메라 2채널 모두 녹화 확인
- 실패/어색한 동작은 즉시 `d`로 버리기
