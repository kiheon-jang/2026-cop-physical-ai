# 주간 정리 — 2026-05-31 (W4주차)

## 이번 주 완료 작업
1. 자동 데이터 수집 스크립트 실행 및 테스트 완료
2. Pick-Place 시나리오 시뮬레이션 동작 및 비디오 생성 완료
3. LeRobot Dataset 포맷으로 50 에피소드 데이터 합성 완료
4. Phase 0 완료 리포트 작성 완료
5. 6-DoF 애니메이션 비디오 생성 완료
6. 카메라 이미지 캡처 및 저장 완료

## 핵심 메트릭
- `sim_data_collector.py` 50 에피소드 데이터 수집 성공률: 100%
- `sim_data_collector.py` 50 에피소드 수집 시간: 약 3분 (에피소드당 평균 3.6초)
- `sim_data_collector.py` 생성 데이터셋 크기: 약 1.5GB

## 미완료 / 다음주 이월
- `sim_data_collector.py` `--num_episodes` 플래그 적용 여부 확인
- Phase 1 (사전학습) 준비 및 ACT 학습 파이프라인 구성