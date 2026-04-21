# 📋 샘플코드 완성도 현황판 (SAMPLE_STATUS.md)

> 자동 업데이트: 매일 23:30 크론 + 매주 일요일 주간검수 크론  
> 완성도 기준: [CONTRIBUTING.md](../CONTRIBUTING.md) 참조

---

## 전체 현황

| 카테고리 | 완성 | 기본 | 작성중 | 계획 |
|---------|------|------|--------|------|
| unit/ | 2 | 0 | 0 | 5 |
| hardware/ | 0 | 1 | 0 | 3 |
| training/ | 0 | 0 | 0 | 4 |
| inference/ | 0 | 0 | 0 | 2 |

---

## unit/ — 하드웨어 없이 실행

| 파일 | 상태 | 완성도 | 마지막 검증 | 설명 |
|------|------|--------|------------|------|
| `test_follower_basic.py` | ✅ 완성 | ⭐⭐⭐ | 2026-04-21 | 모터 6개 ID/각도 범위 검증 |
| `test_data_pipeline.py` | ✅ 완성 | ⭐⭐⭐ | 2026-04-21 | 데이터 수집 파이프라인 구조 검증 |
| `test_act_training.py` | 📋 계획 | - | - | ACT 학습 루프 단위테스트 |
| `test_diffusion_training.py` | 📋 계획 | - | - | Diffusion Policy 학습 파이프라인 |
| `test_inference_pipeline.py` | 📋 계획 | - | - | 인퍼런스 비동기 루프 |

---

## hardware/ — 실제 로봇 연결 후 실행

| 파일 | 상태 | 완성도 | 마지막 검증 | 설명 |
|------|------|--------|------------|------|
| `run_connection_check.py` | ✅ 기본완성 | ⭐⭐ | 2026-04-21 | 전체 하드웨어 연결 상태 확인 |
| `run_home_position.py` | 📋 계획 | - | - | 홈 포지션 이동 |
| `run_teleoperation_test.py` | 📋 계획 | - | - | 텔레오퍼레이션 단기 테스트 |
| `run_camera_check.py` | 📋 계획 | - | - | 카메라 스냅샷 확인 |

---

## training/ — 학습 파이프라인

| 파일 | 상태 | 완성도 | 마지막 검증 | 설명 |
|------|------|--------|------------|------|
| `test_act_training.py` | 📋 계획 | - | - | ACT 학습 파이프라인 |
| `test_diffusion_training.py` | 📋 계획 | - | - | Diffusion Policy 학습 |
| `test_hyperparameter_search.py` | 📋 계획 | - | - | 하이퍼파라미터 탐색 |

---

## inference/ — 인퍼런스

| 파일 | 상태 | 완성도 | 마지막 검증 | 설명 |
|------|------|--------|------------|------|
| `test_inference_pipeline.py` | 📋 계획 | - | - | 인퍼런스 비동기 루프 |
| `test_camera_pipeline.py` | 📋 계획 | - | - | 카메라 입력 전처리 |

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-21 | 최초 작성. unit 2개 완성, hardware 1개 기본완성 |
