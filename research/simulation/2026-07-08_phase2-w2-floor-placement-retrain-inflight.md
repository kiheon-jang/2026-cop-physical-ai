# Phase 2 W2 진입 — 바닥(배치 다양성) 사이클 ACT 재학습 착수 (in-flight) — 2026-07-08

## 오늘 진행 단계
Phase 2 - W2 진입 — **드라이버가 W1(episodes_cl_dr) 사이클을 STAGE=완료/유지로 닫고,
7/7 W1 결론이 지목한 다음 레버 = 배치 다양성(`.next=episodes_floor`, 바닥/받침대 없는 파지)
사이클로 전환 → ACT 재학습 착수(진행중).**

> 로드맵 W2 dated 항목("Zero-shot 실기 추론 → 격차 측정")은 **외부의존 = 장기헌 Orin/실기
> SSH 미수신 지속**(external-dependencies.md) 으로 실기 track 진입 불가. 따라서 sim track 이
> 7/7 W1 실증 결론에 따라 **배치 커버리지 확장 실험(floor placement diversity)** 으로 계속 전진.
> 이 재학습이 "DR 축이 못 올린 sim 성공 천장을 배치 다양성이 실제로 올리는가"의 첫 실측 준비.

## 결정론적 드라이버 결과 (재실행 없음 — 드라이버 담당)
```
타겟: 데이터=episodes_cl_dr  ckpt=checkpoints/act_cl_dr
STAGE=완료/유지  episodes_cl_dr 50ep · 최종 성공률=0.7 (목표 0.90)
  ▶ 예약된 다음 사이클로 전환: data/episodes_floor — 재평가 시작
타겟: 데이터=episodes_floor  ckpt=checkpoints/act_floor
STAGE=학습시작  (episodes_floor 50ep 로 ACT 재학습, 100epoch → checkpoints/act_floor)
[start_act_train] 시작 pid=94316 args=--epochs 100 --no-resume
```

## 실행 상태 검증 (야간 에이전트, 비파괴 관찰만)
- **학습 프로세스 alive**: `pid 94316` = `.venv/bin/python3 scripts/train_act.py --epochs 100`.
  `logs/act_train.log` `train_start`: dataset_root=`data/episodes_floor`, checkpoint_dir=`checkpoints/act_floor`,
  epochs=100, resume_from=null(`--no-resume`), timestamp `2026-07-08T23:00:11`. 현재 **epoch 0 step 10 loss 25.5**
  (막 시작 — 정상 초기 loss). ETA ~익일 새벽(직전 사이클 wall_clock 34291s≈9.5h 참조).
- **데이터셋 실재 확인**: `data/episodes_floor` = **50ep / 3350frame** (info.json), 바닥 파지 씬.
  수집 로그 `logs/cop_data_collect.log`(7/6 17:03): **성공 50/50, 시도 51회, yield 98%**,
  cube 배치 x≈0.11~0.15 / y≈-0.007~0.018 (배치 다양성), lift 56~64mm. 즉 floor 사이클 데이터는
  7/6 주간에 이미 합성(commit `db680ac`/`ce3d0f4`)되어 대기 → 오늘 드라이버가 학습만 트리거.
- **마커 2단계 격리 정상(baseline 무손상)**:
  - `logs/cop_dataset_target` = `data/episodes_floor` (타겟 전환됨)
  - `logs/cop_trained_on.marker` = `episodes_cl_dr:1783181837` (**직전 승격값 유지** — 운영
    `rollout_summary.json` 은 여전히 DR-trained 성적. 학습 미완이라 미덮어씀)
  - `logs/cop_trained_on.marker.pending` = `episodes_floor:1783324998` (신규, **승격 대기**)
  - → 6/22 SILENT 멈춤 반대·설계대로: 학습 완료 전까지 baseline 측정 결과 불변. 드라이버가
    학습완료 인식 시 pending 승격 + `act_floor/epoch_0099` 측정.
- **체크포인트 격리**: `checkpoints/` = `act`(open-loop) · `act_cl_dr`(DR-trained) · `act_floor`(신규 학습중)
  → 3자 분리, 상호 파괴 없음.

## 관찰 / 이슈
- **왜 floor(바닥 파지)가 배치 다양성 레버인가**: W1(7/1~7/7)은 4개 프록시 + DR 실모델 재학습으로
  **병목 = 섭동강건성이 아니라 큐브배치 커버리지(모방격차)** 를 확증(7/7 로드맵/로그). DR 축 증강은
  성공률 천장(0.825↔0.800)을 못 올림. floor 씬은 받침대를 없애 큐브가 바닥 전역에 놓이며 배치
  분포를 넓힘 → 학습 데이터의 배치 다양성↑ = 7/7 이 지목한 정공법의 첫 실측.
- **로드맵 정합**: W2 dated(zero-shot 실기)는 Orin SSH 외부의존 미수신으로 실기 진입 불가 →
  sim track 이 floor 사이클로 전진. 이는 로드맵 W2 real-robot 스텝 대체가 아니라, W1 결론을 잇는
  드라이버 `.next` sim 사이클(sim 천장 검증). 실기 track 은 SSH 수신 시 재개.
- **[자가치유] 없음** — 어제(7/7) research-log·로드맵 최신, 드라이버 STAGE 정상(완료→전환→학습시작),
  마커 격리 정합, 데이터셋 실재, 학습 프로세스 alive, 에러 로그 없음.
- 참고: `data/episodes_floor.bak-20260706-170110` = 수집 시 안전 백업(정상), `SO-ARM100`(untracked
  nested repo)·`docs/.../2026-07-08.html`(대시보드 산출물)은 git add 대상 판단 시 서브모듈/대시보드
  규칙 준수(SO-ARM100 은 main repo add 금지).

## 다음 단계 (드라이버 담당 — 야간 에이전트 재실행 금지)
- **학습 완료 시**: pending(`episodes_floor:1783324998`) 승격 → `cop_trained_on.marker` 갱신 →
  `act_floor/epoch_0099` 측정 → floor-trained rollout 성적 산출. baseline(episodes_cl_dr)은
  `rollout_summary_baseline_cl.json` 계열로 보존.
- **비교 검증(향후)**: floor-trained 를 동일 4 seed(42/7/123/2026) 공정추정으로 baseline·DR-trained 와
  비교. **핵심 질문**: 배치 다양성 데이터가 성공률 천장(0.80~0.825)을 실제로 올리는가, 실패
  큐브배치({2,5,8}·{0,1}·{5})가 이동/축소되는가. 올리면 7/7 모방격차 가설의 처방 실증.
- 실기 track(W2 zero-shot): Orin/실기 SSH 수신 시 재개 — external-dependencies.md 미수신 지속 감시.
