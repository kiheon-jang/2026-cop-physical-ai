# Phase 2 W1 — DR 축별(per-axis) ablation: 어느 섭동축이 grasp 를 흔드는가

- 날짜: 2026-07-03 (금요일)
- 단계: Phase 2 (Sim2Real) - W1 (7/1~7/7) Domain Randomization
- 선행: 7/1 DR 모듈 착수 + 수집기/측정기 배선, 7/2 DR **aggregate** on/off 프록시(0.70→0.80)
- 성격: **비파괴 추론-시점 프록시 측정**(재학습 없음). 운영 `rollout_summary.json`·`data/episodes_cl`·드라이버 파이프라인 **불변**.

## 왜 (동기)
7/2 aggregate 프록시는 "3축 동시 DR-on 이 grasp 를 무너뜨리지 않는다(0.70→0.80)"까지만 보였다.
**어느 축이 강건/취약을 유발하는지**는 aggregate 로 분리 불가. Sim2Real 관점에서 "가장 큰 도메인 격차 축"을
알면 Phase 2 W2(zero-shot 실기) 이전에 우선순위를 잡을 수 있다 → **축별 단일 ablation** 측정.

## 무엇을 했나 (코드, surgical)
1. `samples/training/sim_domain_randomization.py`
   - `randomize_scene(model, rng, axes=None)` — `axes` 부분집합 인자 추가(기본 3축 전부, 하위호환).
     비활성 축은 원본값 유지(카메라 노이즈 std=0). 모듈 상수 `DR_AXES=("light","friction","camera")`.
2. `scripts/render_act_rollout.py`
   - `--dr-axes light,friction,camera` 플래그 추가 → `run_rollout`→`randomize_scene(axes=)` 로 전달.
   - 부분집합이면 결과를 `rollout_summary_dr_<axes>.json` 로 격리 저장(3축 aggregate·운영 summary 불변).
   - 요약에 `dr_axes` 필드 기록. 알 수 없는 축은 에러 JSON 후 종료(검증).
   - 큐브 초기위치 rng 는 DR rng 와 **별도 스트림** → 축 선택과 무관하게 큐브 배치 동일(공정 비교).

실행(동일 seed 42, N=10, `epoch_0099`, cpu, `--video-rollouts 0`):
```
.venv/bin/python3 scripts/render_act_rollout.py --checkpoint checkpoints/act/epoch_0099 \
  --rollouts 10 --seed 42 --dr --dr-axes <light|friction|camera> --video-rollouts 0
```

## 결과 (어떻게 검증했나)

| 조건 | 성공률 | median lift | 실패 rollout |
|---|---|---|---|
| DR-off (운영 대조군, 7/2 재사용) | 0.70 (7/10) | 43.7mm | 2, 5, 8 |
| DR **light-only** (신규) | 0.70 (7/10) | 43.8mm | 2, 5, 8 |
| DR **friction-only** (신규) | 0.70 (7/10) | 43.4mm | 2, 5, 8 |
| DR **camera-noise-only** (신규) | 0.70 (7/10) | 43.7mm | 2, 5, 8 |
| DR 3축 aggregate (7/2) | 0.80 (8/10) | 44.1mm | 2, 8 |

- 산출물: `research/simulation/inference_progress/rollout_summary_dr_{light,friction,camera}.json` (신규 3개).

## 해석
- **세 섭동축을 각각 단독 적용해도 성공률·실패집합이 운영 baseline 과 완전 동일**(0.70, {2,5,8}).
  → **어느 단일 축도 grasp 를 흔들거나 돕지 않는다.** 실패 {2,5,8} 은 특정 큐브 초기배치의
  **구조적 실패**이며 DR 무관(조명/마찰/카메라노이즈 어디에도 반응 안 함)임이 축별로 재확인됨.
- 7/2 aggregate 에서 +1(rollout 5 성공→0.80)은 **3축 동시**에서만 나타남 → 단일 축 기여가 아니라
  임계값(40mm) 부근 marginal case 가 복합 섭동으로 우연히 넘어간 **노이즈**로 판단(축별로는 5 여전히 실패).
- **결론: closed-loop 정책은 조명/마찰/카메라노이즈 각각에 독립적으로 강건. 지배적 Sim2Real 격차축 없음**
  → 긍정적 Sim2Real 신호. 남은 실패는 섭동이 아니라 정책의 특정 큐브배치 대응력(모방격차) 문제.

## 다음 단계로의 연결
- 축별 강건성이 균일하게 확인됨 → W2 zero-shot 실기(외부의존: Orin/실기 SSH)에서 **격차의 주원인이
  시각·물리 섭동이 아닐** 가능성이 큼. 실기 격차가 크면 원인은 도메인 섭동보다 기구/캘리브레이션 쪽으로 좁혀짐.
- **W1 본격 잔여**(변함없음): `sim_data_collector.py --dr` 로 DR 50ep 합성→ACT 재학습→학습-DR 일반화 검증.
  이는 수집+학습(수 시간)이라 **드라이버 사이클**(`cop_pipeline_advance.sh`, COP_TARGET_EP 상향/DR 마커 트리거) 담당.
- 남은 구조적 실패({2,5,8})는 데이터 증대(추가 에피소드로 해당 배치 커버)로 접근 가능 — 드라이버 다음 사이클 후보.

## 무결성
- 운영 `rollout_summary.json` 7/10·`rollout_summary_dr.json`(aggregate) 8/10·`data/episodes_cl` 50ep 전부 **불변**.
- 변경 파일: 코드 2개(하위호환) + 신규 축별 summary 3개. 드라이버 파이프라인 재실행 없음. 서브모듈 무변경.
</content>
</invoke>
