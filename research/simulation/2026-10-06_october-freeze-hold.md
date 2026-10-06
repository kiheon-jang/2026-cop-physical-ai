# 2026-10-06 — 10월 동결 유지 + 드라이버 STAGE 문서화 + 비파괴 sanity

## 맥락
10월 = 시연 + 사내 발표 (phase 외부). Phase 작업은 9월에 완료.
PHASE_ROADMAP 잔여 `[ ]` 은 전부 **보류 / 외부 의존 / PARA 읽기전용 / 물리 리허설** →
야간 시뮬 에이전트 대상 아님. 신규 시뮬 구현 작업 없음.

로드맵 10월 마감 잔여 2건:
- **985 pptx 활동현장 슬라이드 이미지** — frontmatter `site_image:` 입력이 PARA 읽기전용 →
  사용자 직접. (시뮬 추론 스틸 `_20260918.mp4` 공칭 사용 지침은 로드맵에 명시됨)
- **989 리허설** — 1차 전체 25분 계측 / 2차 폴백 경로 = 물리 행위 → 외부 의존.

## 드라이버 STAGE (이미 실행됨 — 재실행 금지)
```
STAGE=완료/유지  데이터 episodes_rs232 100ep · 최종 성공률=0.6 (목표 0.50)
타겟: 데이터=episodes_rs232  ckpt=checkpoints/act_rs232_sim
```
새 사이클 미트리거 → 수집/학습/측정 재실행 없음.

## 동결 무결성 검증 (비파괴)
| 항목 | 값 | 상태 |
|---|---|---|
| `episodes_rs232` total_episodes | 100 | 불변 |
| 모델 락 `act_rs232_sim/epoch_0041/model.safetensors` | mtime **Sep 18 02:42**, 335,947,896 B | 불변 |
| 마커 trained_on | `episodes_rs232:1789546321` | 정합 |
| 마커 measured | `episodes_rs232:1789666953` | 정합 |
| pending 마커 | 없음 | 정상 (대기 사이클 없음) |
| dataset target | `data/episodes_rs232` (`.next` 없음) | 불변 |
| `rollout_summary_rs232.json` | seed42 **0.600 / median_lift 9.66mm**, mtime **Oct 2** | 재측정 없음 |

→ 학습·측정·판정·환경 **변경 0**. 공표값 0.600 불변.

## 비파괴 sim sanity (MuJoCo 3.8.0 건재)
- `sim/assets/rs232_unplug_scene.xml` 로드 OK — nq=7, nu=6, ncam=3.
- headless `mujoco.Renderer(240×320)` 렌더 OK — shape (240,320,3) uint8.
- (참고) `scene_grasp_pads.xml` 등 SO-ARM100 서브모듈 씬도 로드 정상.

## 다음 단계
- 시뮬 트랙 동결 유지. 10월 잔여는 비시뮬(사용자 직접 pptx 이미지 + 물리 리허설).
- 드라이버 STAGE=완료/유지. 새 사이클 조건(마커 삭제 / 타겟 전환) 미세팅 → 진행 없음이 정상.
