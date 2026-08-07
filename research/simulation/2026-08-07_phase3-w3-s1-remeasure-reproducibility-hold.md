# Phase 3 W3 — S1 리셋버튼 4-seed 재측정 재현성 확인 + W4 hold (2026-08-07)

## 오늘 진행 단계
Phase 3 - W3 - S1 ACT 정책(`act_s1_sim/epoch_0029`) 롤아웃 재측정 (완료/유지).
W3(dated 8/19~8/25)는 8/6 조기 완주. 실행 가능한 dated 항목은 전부 소진 →
다음 pending = W4(8/26~) sim2real omen 핸드오프(외부 협업 의존, 진입 불가).

## 실행 테스트 결과
드라이버(`cop_pipeline_advance.sh`) STAGE=측정 — **파이프라인 수집/학습 재실행 없음**.
어제(8/6 14:48) 측정한 동일 체크포인트를 오늘 밤(8/7 23:01~23:03) 4-seed 재측정.

- 체크포인트: `checkpoints/act_s1_sim/epoch_0029` → 드라이버가 측정 후
  `epoch_0029_measured_0.925.bak` 로 승격 복제(둘 다 존재, 측정 산출물 스탬프).
- **4-seed 재측정 (N=10, cpu, LED-latch 자동채점)**:
  - seed42  9/10 = **0.90** (23:01:37)
  - seed7   9/10 = **0.90** (23:02:16)
  - seed123 10/10 = **1.00** (23:02:56)
  - seed2026 9/10 = **0.90** (23:03:35)
  - **평균 0.925 (37/40)** — 8/6 최초 측정과 완전 동일(재현성 확인).
- median press 3.37~3.7mm (임계 1.5mm 위, 여유).
- 산출물: `rollout_summary_s1[_seed{7,123,2026}].json` 4종 갱신(측정시각·ckpt명·wall_clock만 변경, 성공률/판정 불변),
  history 5종 신규(`20260807-2301..2303_*_measured_0.925.bak*`, seed42 traj 포함).

## 검증
```
rollout_summary_s1.json          seed 42   success_rate 0.9   measured_at 2026-08-07T23:01:37
rollout_summary_s1_seed7.json    seed 7    success_rate 0.9   measured_at 2026-08-07T23:02:16
rollout_summary_s1_seed123.json  seed 123  success_rate 1.0   measured_at 2026-08-07T23:02:56
rollout_summary_s1_seed2026.json seed 2026 success_rate 0.9   measured_at 2026-08-07T23:03:35
```
git diff 확인: 4종 요약 변경분 = `checkpoint`(→`.bak`), `measured_at`, `wall_clock_sec`, `dr_axes:null` 필드 추가뿐.
per-rollout 판정·press_depth 불변 → **결정론적 재현**(같은 seed·같은 ckpt → 같은 결과).

## 관찰 / 이슈
- Phase 3 완료 기준 "성공률 70%(LED 자동판정)" 재측정으로도 충족(0.925). 남은 기준 =
  "합성 데이터셋 omen 로드 확인"(W4 외부 협업).
- **S1 정책 DR 강건성 신호(어제 커밋된 8/7 02:xx 산출물, 참고)**: `rollout_summary_s1_dr*` 은
  DR-on 시 성공률 하락(4-seed aggregate ~0.45, per-axis light 0.6·friction 0.8·camera 0.8) —
  pick-place floor 정책(DR 강건, 7/3)과 대조적으로 **S1 정책은 조명·마찰·카메라노이즈에 민감**.
  → Sim2Real 격차 관측치로 W4 핸드오프 보고에 반영할 후보(오늘 밤 신규 작업 아님, 재실행 안 함).
- [자가치유] 없음. 어제 research-log 존재, 로드맵 동기 정상.

## 다음 단계
- **W4(8/26~) sim2real omen 핸드오프**: `act_s1_sim/epoch_0029` + `episodes_s1` omen 전달,
  P1 LED ROI 캘리브 지원, Sim2Real 격차 보고(위 DR 민감도 포함).
- W2 잔여 omen lerobot 0.6.1 로드 스모크(외부 의존, W4 병합 가능).
- Phase 2 잔여 2건(zero-shot 실기=W4 이관 / full-epoch=04:04 killer 8/6 종결)은 외부 의존 대기.
