# RS232 ACT 재학습 진행 문서화 (Day 2, in-flight) — 2026-09-17

Phase 4 - W2 - RS232 ACT 재학습(케이블 출구 실기 정합 + 핀치 판정 재수집본). 드라이버 STAGE=**학습중**.
어제(9/16) epoch 7/42 착수 → 오늘 epoch 37/42. 학습·측정 재실행 없음(드라이버 소유), 관측·문서화만.

## 드라이버 STAGE 결과 (재실행 아님, 관측만)

- STAGE=**학습중**. `pid=48360 alive=yes`, state `Us`(세션 분리 = 04:04 killer 회피 유효), 시작 9/16 17:13.
- `train_act.py --epochs 42` → `checkpoints/act_rs232_sim`, dataset_root=`data/episodes_rs232` (케이블 출구 정정 재수집본 100ep/16,093f).
- 라이브 **epoch 37/42**(36 완료), step 800 loss **0.00904**(l1 0.00784, kl 0.000119). log mtime 9/17 23:00, age ~11s = alive.
- 수렴 곡선 정상: epoch 7 loss 0.0431 → epoch 37 0.0090, from-scratch(`--no-resume`) 곡선. epoch당 ~2,900s.

## 체크포인트 무결성 검증 (오늘의 핵심 관측)

드라이버 출력의 `ckpt_latest=epoch_0041`(Sep 13) 과 라이브 epoch 37 이 언뜻 불일치로 보여 직접 검증:

- **디렉터리 mtime 은 Sep 12~13 로 고정** — 언뜻 새 run 이 저장 안 하는 것처럼 보이나, 이는 `save_pretrained` 가 기존 dir 안 `model.safetensors` 를 **덮어쓰기**(파일 수정)라 **dir mtime 은 갱신 안 됨**(macOS: dir mtime 은 엔트리 추가/삭제/rename 시만). 9/16 로그·6/25 로그가 기록한 알려진 특성, 결함 아님.
- **내부 파일 mtime 으로 신선도 확증**:
  - `epoch_0009/model.safetensors` = **Sep 17 00:59** (새 run 저장)
  - `epoch_0029/model.safetensors` = **Sep 17 17:04** (새 run 저장)
  - `epoch_0041/model.safetensors` = Sep 13 04:57 (직전 완료 run — 새 run epoch 37 이라 idx 41 미도달, 정상)
- **로그 확증**: `logs/act_train.log` 에 `{"checkpoint_saved": ".../epoch_0019"}`, `.../epoch_0029` 기록 존재. 저장 규칙 `(epoch+1)%10==0 or ==epochs` → idx 9/19/29/39 + final 41. 새 run 은 9/19/29 저장 완료, 다음 저장 idx 39, 최종 41.
- **결론**: 케이블 정정 모델이 정상 저장 중. ETA = 잔여 5 epoch × ~2,900s ≈ 4h → **~03:00~03:30 KST 9/18** 완주(04:04 killer 이전 + 세션 분리로 안전).

## 마커·baseline 무결성 격리 (설계대로)

- `cop_trained_on.marker` = `episodes_rs232:1789126035` (정정 前 완료 run, 승격됨)
- `cop_trained_on.marker.pending` = `episodes_rs232:1789243031` (정정 재학습, **대기·미승격**)
- `cop_measured.marker` = `episodes_rs232:1789243031` (9/16 churn 해소용 기록값)
- `cop_dataset_target` = `data/episodes_rs232`
- 학습 미완 → 승격/측정 보류(6/22 SILENT 반대·설계대로) → baseline 무손상:
  `rollout_summary_rs232.json` mtime **Sep 15 23:02**(seed42 0.9/0.7)·`cop_rollout.log` **Sep 15 23:06** 불변 = 야간 측정 미실행.

**신규 모델 측정 누락 위험 없음**: MODEL_SIG = `DS_BASE:최신 ckpt 내부 최신 mtime` 라, 재학습이 epoch_0041 를 ~03:00 덮어쓰면 mtime 갱신 → measured(`1789243031`)와 불일치 → 드라이버가 정정 epoch_0041 을 **자동 재측정**(핀치 판정 + `*_nopinch_legacy` 병기). dataset-sig 기반 아님 → measured==pending 이어도 스킵 안 됨.

## 이월 항목 해소 — 근단 실패 분해용 플러그 좌표 덤프

9/13~9/16 "다음 단계"의 *측정기에 rollout 별 플러그 초기좌표 덤프 추가 → 근단(x<0.19) 실패 배치 분해* 는
**이미 충족됨** — 코드 추가 불필요:

- `render_act_rollout_rs232.py` 의 per-rollout 레코드가 이미 `"pcb": placement` 를 덤프하고, `placement` =
  `{"x","y","yaw_deg","rejected"}`(`sim_rs232_unplug.Rs232UnplugTwin.reset` 반환). 커넥터/포트는 PCB body 자식이라 `pcb.x` = 플러그 초기 x.
- 즉 근단(x<0.19) vs 원단 실패 분해는 **기존 summary/trajectory 덤프에서 직접 가능**. 정정 모델이 드라이버에 의해
  측정되면(내일) `pcb.x` 필터로 근단 실패율 산출 가능. (ponytail: 존재하는 필드 재사용, 측정기 변경 없음.)

## 헬스체크

- 학습(MPS ~8.6GB, rss ~0.9GB 평탄, OOM/누수 없음), 로그 정상 수렴.
- [자가치유] 없음(에러 없음). [의도적 skip] Phase 0 레거시 `sim_pick_place.py`/`sim_data_collector.py` 미실행(RS232 무관 + 학습 중 데이터 쓰기 경합 회피).

## 다음 단계 (연결)

- 학습 완주(~03:00 9/18) → 정정 epoch_0041 새 mtime → MODEL_SIG 갱신 → 드라이버 자동 재측정(핀치 + `*_nopinch_legacy` 병기) → 4-seed(42/7/123/2026) 공정추정 → 새/옛 기준 수치 병기 보고 → 사이트 갱신.
- 이후 로드맵 855 `[ ]` **RS232 DR 합성 + 재학습**(드라이버 새 사이클) — 단 정정 baseline 측정 확정 후 착수(stale baseline 비교 방지).
- 실기 실측 대기: HHT 플러그 분리력·잭스크류 체결, closeup 카메라(손목 장착) 자세, 서보 강성.
