# 10월 동결 유지 + 비파괴 sanity — 2026-10-05 (월요일)

## 맥락
10월은 phase 외부(시연 + 사내 발표). PHASE_ROADMAP 10월 절(978)은 **학습·측정·판정·환경
불변**을 명시한다. 모델 락 = `act_rs232_sim/epoch_0041`(공표 0.600).

로드맵 잔여 미체크(`[ ]`) 항목을 문서 순서로 훑으면 야간 시뮬 에이전트가 할 actionable
시뮬 구현 항목은 **없다**:
- 985 **10월 pptx 활동현장 이미지** — frontmatter `site_image:` 입력이 PARA 읽기전용 →
  사용자 직접(외부 의존).
- 989 **리허설** — 물리 활동(10월 W2~W3).
- 그 외 924/934~938 등은 전부 *외부 의존 보류* / *이관* 태그.

→ 신규 MJCF/수집기/expert 코드 작성 없음. 동결 유지 + 비파괴 sanity 만 수행.

## 드라이버 STAGE 결과 (드라이버가 결정론적으로 실행함 — 재실행 안 함)
```
타겟: 데이터=episodes_rs232  ckpt=checkpoints/act_rs232_sim
STAGE=완료/유지  episodes_rs232 100ep · 최종 성공률=0.6 (목표 0.50)
```
수집/학습/측정 재실행 없음. 한 사이클 완료 상태 유지.

## 동결 무결성 검증 (비파괴)
- `episodes_rs232` total_episodes = **100** 불변.
- 모델 락 `checkpoints/act_rs232_sim/epoch_0041/model.safetensors` mtime **Sep 18 02:42** 불변.
- 마커 3종 정합: target=`episodes_rs232` · trained_on=`episodes_rs232:1789546321` ·
  measured=`episodes_rs232:1789666953`. pending 없음.
- `rollout_summary_rs232.json` seed42 **rate=0.600 / median_lift 9.66mm**, mtime **Oct 2**
  (재측정 없음).
- git 시뮬 산출물(research/simulation·checkpoints·data) 무변경.

## 비파괴 sim sanity (3/3 렌더 정상)
baseline(rollout_summary*, checkpoints/act_rs232_sim, episodes_rs232) 무접촉. 세 스크립트
모두 `research/simulation/video/` 에만 기록.

| 스크립트 | 결과 |
|---|---|
| `sim_pick_place.py` | status=fail, min_approach 0.323m, max_lift 0.0m — **알려진 상태**(6월 root-cause: 고정포즈 open-loop expert 가 큐브 ~5cm 미달). 실제 grasp 는 closed-loop/ACT 담당. 회귀 아님. video 저장 정상 |
| `sim_camera_verification.py` | 30프레임 양 카메라(overhead+gripper) 캡처·저장 정상 |
| `sim_headless_6dof_video.py` | 6관절 애니 2501프레임, mp4 저장 정상 |

MuJoCo 3.8.0 headless 파이프라인 건재. (`sim_data_collector` = 데이터셋 기록 → 동결 중
SKIP. `sim_viewer_6dof` = headless 비호환 SKIP.)

## 다음 단계
- 10월 잔여는 비시뮬: 985 pptx 활동현장 이미지(사용자 직접) + 989 리허설(물리, W2~W3).
- 시뮬 트랙 동결 유지. 드라이버 다음 사이클은 `logs/cop_dataset_target(.next)` 전환 또는
  마커 삭제 시에만 — 10월엔 미세팅(의도적 동결).
