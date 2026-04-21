# Hardware 샘플 — 실제 로봇 연결 후 실행

> ⚠️ **이 폴더의 코드는 실제 하드웨어가 연결된 상태에서만 실행하세요.**  
> 단위테스트용 코드는 `../unit/` 폴더를 사용하세요.

## 실행 전 체크리스트

```
□ 1. Follower USB 연결 확인 (lerobot-find-port)
□ 2. Leader USB 연결 확인 (lerobot-find-port)
□ 3. Follower 전원 공급 확인 (12V)
□ 4. Leader 전원 공급 확인 (7.4V or USB)
□ 5. 캘리브레이션 파일 존재 확인
□ 6. 카메라 2개 연결 확인
□ 7. 로봇 팔 주변 공간 확보 (반경 50cm)
□ 8. 비상정지 방법 숙지 (Ctrl+C)
```

## 포트 확인 방법
```bash
# 연결된 포트 자동 감지
lerobot-find-port

# 예상 출력:
# The port of this MotorsBus is '/dev/tty.usbmodem5AE60573201'  ← Follower
# The port of this MotorsBus is '/dev/tty.usbmodem5AE60537131'  ← Leader
```

## 파일 목록

| 파일 | 설명 | 소요시간 |
|------|------|--------|
| `run_connection_check.py` | 연결 및 모터 상태 확인 | ~30초 |
| `run_home_position.py` | 홈 포지션 이동 | ~5초 |
| `run_teleoperation_test.py` | 텔레오퍼레이션 단기 테스트 | ~60초 |
| `run_camera_check.py` | 카메라 스냅샷 확인 | ~10초 |
