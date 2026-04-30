# Phase 0 킥오프 — 시뮬 환경 셋업 시작

> 작성일: 2026-05-01
> Phase: 0 (시뮬 환경 셋업)
> 주차: W1 (5/1 ~ 5/7)

## 목적

10월 PCB 제품 조정 + RS232 HHT 결선 시연을 위한 시뮬 학습 환경 구축. Mac Mini M5 단독으로 진행 가능하도록 설계.

## 결정 사항 (2026-05-01)

| 항목 | 결정 | 사유 |
|------|------|------|
| 시뮬레이터 | **MuJoCo 3.x** | Apple Silicon 네이티브, Isaac Lab은 NVIDIA GPU 필수 |
| 모델 | TheRobotStudio SO-ARM100/101 MJCF | 공식 오픈소스, LeRobot 통합 |
| 학습 머신 | Mac Mini M5 16GB | 단독 처리 가능 (시뮬+학습+메트릭) |
| 실기 검증 | 별도 머신 (Orin Nano) | 학습 모델만 git push → 실기 추론 |
| 카메라 | 시뮬 가상 카메라 2대 | Mac Mini에 실기 연결 불필요 |

## Phase 0 W1 작업 계획

| 일자 | 작업 | 산출물 |
|------|------|--------|
| 5/1 | MuJoCo 설치 + Apple Silicon 호환성 검증 | 설치 로그 |
| 5/2 | SO-ARM100 MJCF 다운로드 + 디렉토리 구성 | 모델 파일 |
| 5/3 | viewer로 6-DoF 동작 확인 | 스크린샷 |
| 5/4 | Joint limits 적용 (STS3215 사양) | 수정된 MJCF |
| 5/5 | 그리퍼 추가 + 동작 확인 | 시뮬 영상 |
| 5/6 | 단순 동작 시연 스크립트 | `samples/training/sim_basic_motion.py` |
| 5/7 | W1 정리 + W2 카메라 셋업 준비 | W1 리포트 |

## 외부 의존 (현재)

차단 항목 — `agent/external-dependencies.md` 참조:
- [ ] [전체] MuJoCo 사내 사용 라이선스 확인 (마감 5/3)
- [ ] [실기 담당] 웹캠 캘리브레이션값 측정 (마감 5/14, W2 차단)
- [ ] [실기 담당] SO-ARM101 실측 무게/마찰 측정 (마감 5/21, W3 차단)

## 참고 자료

- MuJoCo 공식 문서: https://mujoco.readthedocs.io/
- SO-ARM100 모델: https://github.com/TheRobotStudio/SO-ARM100
- LeRobot MuJoCo 통합: https://huggingface.co/lerobot
- ACT 논문: https://tonyzhaozh.github.io/aloha/
- Diffusion Policy 논문: https://diffusion-policy.cs.columbia.edu/

## 다음 단계

5/1 23:00 Hermes 첫 시뮬 크론에서 W1 D1 작업 시작:
1. MuJoCo 설치 (`uv pip install mujoco`)
2. Apple Silicon 호환성 검증 (`python -c "import mujoco; print(mujoco.__version__)"`)
3. 결과를 `research/simulation/01_mujoco-install.md`에 기록
4. Obsidian Vault에 미러
5. git commit + push
