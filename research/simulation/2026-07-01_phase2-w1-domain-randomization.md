# Phase 2 W1 — Domain Randomization 기반 모듈 착수 (2026-07-01)

> Phase 1(6월 sim 사전학습) 종료 → **7월 Phase 2(Sim2Real) 진입 첫날**.
> PHASE_ROADMAP Phase 2 W1 = **Domain Randomization (조명, 마찰, 카메라 노이즈)**.

## 0. 야간 파이프라인 드라이버 상태 (재실행 없음)
결정론적 드라이버 `scripts/cop_pipeline_advance.sh` (01:00):
```
STAGE=완료/유지  데이터 50ep · 최종 성공률=0.7 (목표 0.90)
```
- 마커: `logs/cop_trained_on.marker`(6/24) · `logs/cop_measured.marker`(6/25) → 현 체크포인트 정합, 재학습/재측정 없이 **유지**.
- `rollout_summary.json`: 10 rollout 중 7성공 = **0.70**, median lift **43.7mm**, scene=`scene_grasp_pads.xml`, device=cpu.
- Phase 1 cycle1 은 홀딩 유지(70%) — 본 회차는 파이프라인 재실행 없이 **Phase 2 W1 신규 작업**을 진행.

## 1. 오늘 한 일
Sim2Real 격차 축소의 첫 빌딩블록인 **Domain Randomization 모듈**을 신규 작성:
`samples/training/sim_domain_randomization.py` (headless 전용, viewer 호출 없음).

세 축을 무작위화 (W1 명세 그대로):
| 축 | 방법 | 범위 |
|---|---|---|
| 조명 | `model.light_diffuse/ambient` 강도 + `light_pos` XY 지터 | diffuse 0.4~0.8, ambient 0.2~0.45, 위치 ±0.5m |
| 마찰 | `model.geom_friction[:,0]` 슬라이딩 마찰 곱셈 지터 | ×0.7~1.3 |
| 카메라 | 렌더된 RGB 에 가우시안 센서 노이즈 | std 2~10 (0–255) |

설계: 모델 로드 후 `model.*` 배열을 in-place 수정 → `renderer.update_scene()` 가 그대로 반영.
공개 API 2종 — `randomize_scene(model, rng)` / `apply_camera_noise(img, std, rng)` — 으로
다음 단계에서 `sim_data_collector.py` / `render_act_rollout.py` 가 reset 마다 호출하도록 연결 가능.

## 2. 검증 방법 / 결과
`_self_test()` 로 8 샘플 무작위화·렌더 (씬: `scene_grasp_pads.xml`, overhead_camera):
- **적용 범위(8 샘플 min/max)** — 전부 설정 범위 내:
  - light_diffuse 0.437~0.708 / light_ambient 0.206~0.392
  - friction_scale 0.802~1.208 / camera_noise_std 3.473~9.966
- **DR 실제 반영 증거**: 프레임 평균 밝기가 110.3~124.7 로 light_diffuse 와 상관(조명 무작위화 입증),
  std~50 의 가우시안 그레인 육안 확인(카메라 노이즈 입증).
- 샘플 프레임 8장: `research/simulation/dr_samples/dr_sample_00~07.png` (640×480).
  - 대표: `dr_sample_04.png` (저조도, mean 110.3) — 팔/테이블/큐브 정상 렌더 + 노이즈 그레인.

## 3. 다음 단계 연결
- **W1 잔여**: `randomize_scene()` 를 `sim_data_collector.py` 의 에피소드 reset 훅에 연결 →
  DR 적용 데이터셋(`data/episodes_cl_dr`) 합성. 측정기 `render_act_rollout.py` 도 동일 DR 적용.
- **W2(zero-shot 실기 추론 → 격차 측정)**: 실기 SSH(외부 의존, 장기헌) 수신 시 진행.
  미수신 시 sim 내 DR-on/off rollout 성공률 비교로 robustness 프록시 측정.
- Phase 1 70%→90%+ 향상(데이터 50→200ep)도 DR 데이터 증대와 함께 자연스러운 후속.

## 관찰 / 이슈
- 독립 무작위화를 위해 매 샘플 모델을 새로 로드(곱셈 누적 방지). 데이터 수집기 연결 시에도
  에피소드 reset 마다 모델 재로드 또는 원본 friction 캐시 후 곱셈 적용 필요 — W1 연결 시 반영.
- [자가치유] 없음.
