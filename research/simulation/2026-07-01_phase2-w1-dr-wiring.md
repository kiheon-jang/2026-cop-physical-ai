# Phase 2 W1 — DR 를 수집기/측정기에 연결 (2026-07-01, 야간 회차)

> 같은 날 01:00 회차가 DR 모듈(`sim_domain_randomization.py`)을 신규 작성·검증(8샘플)했다
> ([2026-07-01_phase2-w1-domain-randomization.md](./2026-07-01_phase2-w1-domain-randomization.md)).
> 본 야간 회차 = 그 다음 W1 항목 **"DR 를 `sim_data_collector.py` reset 훅 + `render_act_rollout.py` 에 연결"** 진행.

## 0. 야간 드라이버 상태 (재실행 없음)
`scripts/cop_pipeline_advance.sh` (23:00):
```
STAGE=완료/유지  데이터 50ep · 최종 성공률=0.7 (목표 0.90)
```
Phase 1 cycle1 홀딩 유지(70%, `rollout_summary.json` 7/10, median 43.7mm). 파이프라인 수집/학습/측정 재실행 없음.
본 회차는 그 위에서 Phase 2 W1 **DR 연결 코드 작업 + 비파괴 스모크**만 수행.

## 1. 오늘 한 일 — DR 연결 (opt-in)
DR 을 **기본 off 인 `--dr` 플래그**로 두 스크립트에 연결. 드라이버는 `--dr` 없이 호출하므로
결정론적 파이프라인(운영 `data/episodes_cl` · `rollout_summary.json`)은 **완전 불변**.

### (a) `sim_domain_randomization.py` — baseline 스냅샷 헬퍼 2종 추가
수집기/측정기는 model 을 **한 번만 로드**하고 매 reset(`mj_resetData`)마다 재사용한다.
friction 은 곱셈(`*=`), light_pos 는 덧셈(`+=`) 이라 restore 없이 매 reset randomize 하면 **누적**된다.
→ `snapshot_baseline(model)` / `restore_baseline(model, baseline)` 추가.
매 reset: `restore_baseline` → `randomize_scene` 순서로 독립 무작위화 보장.

### (b) `sim_data_collector.py` — 에피소드 reset 훅에 연결
- `main(..., use_dr, dr_seed)` 추가. `--dr` / `--dr-seed` CLI.
- 시작 시 `snapshot_baseline` 1회. 매 에피소드: `restore_baseline` → `randomize_scene` →
  `mj_setConst`(마찰 변경을 상수캐시 반영) → 카메라 노이즈 std 를 `record()` 에 전달.
- `record()`: DR-on 이면 렌더 RGB 에 `apply_camera_noise` 적용.

### (c) `render_act_rollout.py` — rollout reset + 관측 RGB 에 연결
- `--dr` 추가. `run_rollout(..., dr_mod, dr_baseline, dr_rng)`.
- 매 rollout: `restore_baseline` → `randomize_scene` → `mj_setConst`, 관측 RGB 에 카메라 노이즈.
- **DR-on 결과는 `rollout_summary_dr.json` 로 별도 저장** → 운영 `rollout_summary.json` 불변.
  (이게 W2 "DR on/off rollout 성공률 비교(robustness 프록시)" 의 기반.)

## 2. 검증 (비파괴 스모크 — 운영 데이터 무접촉)
### 수집기 DR 스모크 (`--dr --root /tmp/... --episodes 2`)
```
[DR] {light_diffuse: 0.655, light_ambient: 0.267, friction_scale: 1.188, camera_noise_std: 9.302}
[성공 1/2] lift=41.8mm frames=67 grasp재시도=1
[DR] {light_diffuse: 0.573, light_ambient: 0.448, friction_scale: 0.802, camera_noise_std: 3.049}
[성공 2/2] lift=42.7mm frames=67 grasp재시도=1
수집 완료: 성공 2/2 (yield 100%)
```
- 두 에피소드 friction 1.188 vs **0.802** — 곱셈 누적 없음(baseline restore 정상).
- DR(조명/마찰/노이즈) 변동 하에서도 closed-loop expert 여전히 grasp 성공 → 수집 파이프라인 DR-ready.

### 측정기 DR 스모크 (`--dr --rollouts 2 --device cpu`)
```
success 2/2 = 1.0, median_lift 45.4mm, dr: true → rollout_summary_dr.json
```
- 학습된 ACT 정책이 DR 변동 관측에서도 성공(2/2, 소표본) → robustness 프록시 측정 경로 확보.

### 무결성 재확인 (스모크 후)
- `data/episodes_cl`: 50ep / 3350frame **무손상** ✓
- `rollout_summary.json`(운영): 7/10 = 0.70 **불변** ✓ / DR 결과는 `rollout_summary_dr.json` 로 격리 ✓
- `py_compile` 3파일 OK. 서브모듈 변경 없음.

## 3. 다음 단계 연결
- **W1 잔여(본격)**: `--dr` 로 DR 데이터셋 50ep 합성(`data/episodes_cl_dr`) → ACT 재학습 → DR-on/off rollout 비교.
  이는 드라이버 사이클(수집→학습→측정, 수 시간)로 진행 — 야간 문서화 회차에서는 재실행하지 않음.
  (드라이버에 DR 사이클을 태우려면 `COP_DATASET_ROOT`/수집 인자에 `--dr` 경로를 태우는 후속 배선 필요.)
- **W2**: zero-shot 실기 추론 → 격차 측정 (외부의존 장기헌 Orin/실기 SSH). 미수신 시 DR-on/off 프록시로 대체.

## 관찰 / 이슈
- friction DR 은 물리를 흔들어 expert yield 를 낮출 수 있으나, 성공필터(lift≥40mm)가 실패를 폐기하므로
  저장 시연은 항상 유효. 조명/카메라노이즈 DR 이 시각 Sim2Real 에 가장 값어치.
- [자가치유] 없음 — 드라이버 STAGE 정상, 마커·산출물 정합, 운영 데이터셋 무손상, 에러 없음.
</content>
</invoke>
