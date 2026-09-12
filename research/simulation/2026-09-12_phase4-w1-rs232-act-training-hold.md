# Phase 4 W1/W2 — RS232 ACT 학습 진행 중 (STAGE=학습중 hold) — 2026-09-12 (토)

## 오늘 진행 단계
Phase 4 - W2 - RS232 ACT 학습 (`data/episodes_rs232` → `checkpoints/act_rs232_sim`).
로드맵 문서순 최초 `[ ]` 실행가능 항목 = W2 line 850 "RS232 ACT 학습". 이 항목이 곧 진행 중인
42-epoch 학습(드라이버 소유). 학습 미완 → 9/12 = 어제 계획대로 **hold day**(문서화·무결성 검증만,
수집/학습/측정 재실행 없음). 신규 시뮬 코드 작업 없음(오늘의 실행가능 항목이 in-flight 학습 자체).

## 실행 테스트 결과 (라이브 증거, 23:00 잡 이후 독립 재확인)
- **학습 진행**: pid **55253** alive, state `Ss`(세션 리더 = PGID 분리, gateway 프로세스 그룹과
  독립 → 04:04 killer 회피 설계 유효). `train_act.py --epochs 42` → `checkpoints/act_rs232_sim`.
  라이브 로그 epoch **34** step 690 loss **0.0099**(l1 0.00833, kl 0.000158) 정상 수렴.
  드라이버 스냅샷(23:00) step 550 → 재확인 시 step 690 = 학습 전진 확인.
- **체크포인트 3개, 신선·균등**:
  - epoch_0009 mtime **04:11** (← 04:04 killer 창을 관통·생존, 세션 분리 fix 실증)
  - epoch_0019 mtime 11:55
  - epoch_0029 mtime 19:39
  - 간격 ~7.7h/10epoch ≈ **2770s/epoch**. 어제 추정(~2783s) 일치.
- **ETA**: epoch 34 @ 23:01 → 잔여 ~7 epoch × 2770s ≈ 5.4h → **≈ 9/13 04:30 KST** 완주.
  다시 04:04 창을 지나지만 세션 분리로 생존 예상.
- **자원**: RSS ~372MB(프로세스), MPS 는 별도 GPU 힙(어제 ~8.6GB). OOM/누수 징후 없음, 16GB 안.

## 무결성 격리 재확인 (마커 3자)
- `logs/cop_dataset_target` = `data/episodes_rs232`
- `cop_trained_on.marker` = `episodes_s1:1785931493` (**불변** — baseline 무손상)
- `cop_trained_on.marker.pending` = `episodes_rs232:1789126035` (대기·미승격)
- `cop_measured.marker` = `episodes_s1:1786060554`
→ 학습 미완이므로 승격/측정 보류(6/22 SILENT 멈춤 반대·설계대로). baseline `act_s1_sim` 무손상.

## 관찰 / 이슈
- [자가치유] 없음(학습 건강, 마커 정합, 체크포인트 신선).
- **[의도적 skip]** 무거운 MuJoCo/렌더 스크립트 미실행: 42-epoch RS232 학습이 16GB 통합
  메모리·MPS 점유 중 두 번째 MuJoCo 프로세스 = OOM 으로 임계 산출물(학습) 죽일 위험 → 보류가
  정공법. 하드룰상 학습 kill/재실행 안 함. RS232 트윈·expert 검증은 9/11 self-check(7/7)로 완료됨.
- 미결(9/11 이월, 9/13 측정 전): 야간 측정 300s timeout 초과 위험(4-seed 40 rollout ≈416s > 300s
  → `cop_measured.marker` 미기록 위험). external-dependencies.md 우선순위2 [장기헌] 결정 대기.
- 미결: jam 사유 문구 정정(서보 토크 한계 아닌 shoulder 링크 기하 간섭), 근단 x<0.19 파지 전략
  (이 충돌 모델 상한 ≈37.5%), 데이터셋 근단 3ep 뿐 → 정책 근단 약세 예상(측정 시 확인).

## 다음 단계 (드라이버)
- 9/13 야간: 학습 완주(ETA 04:30) → pending 승격(`episodes_s1`→`episodes_rs232`) →
  `act_rs232_sim/epoch_0041` 측정 → RS232 4-seed rollout(완전분리·부분성공, x 구간별 실패 분해).
- 측정 wall time 300s 초과 여부 그때 실측. 초과 시 timeout 상향(external-deps 결정 필요).
- 이후 W2: RS232 DR 합성 + 재학습(line 852).
