# Phase 3 W2 — S1 합성 결착 + Phase 2 hold + W3 ACT 인에이블러

> 2026-08-05 (수) 야간 sim 크론. 낮 세션이 Phase 3 W1+W2 를 이미 커밋
> (56cd84f 트윈 4/4 · 7096f13 expert 95% · 88c655c 100ep 합성). 야간 역할 =
> 파이프라인 드라이버 STAGE 결과 문서화 + W3 착수용 미커밋 인에이블러 정리.

## 1. 파이프라인 드라이버 결과 (재실행 없음)
```
타겟: 데이터=episodes_floor  ckpt=checkpoints/act_floor
STAGE=완료/유지  episodes_floor 50ep · 최종 성공률=1.0 (목표 0.90)
```
드라이버는 Phase 2 레거시 타겟(floor)을 계속 완료/유지로 닫는다 — 새 사이클
미트리거. Phase 3(S1) 은 드라이버 상태머신 밖에서 낮 세션이 수동 전진했다.

## 2. 무결성 전수 감사 (비파괴, 이번 세션 도구결과)
- 운영 `research/simulation/inference_progress/rollout_summary.json` md5
  **`5207f67b189645de1bb26c124873b683`** — 7/22~8/04 값과 동일
  (sr 1.0, ckpt `act_floor/epoch_0041`, seed 42, median lift 66.0mm).
- 학습 프로세스 없음 (`pgrep train_act.py` → none).
- md5 CLI sandbox 차단 → `.venv` python hashlib 로 산출.
→ Phase 2 산출물 회귀/오염 0.

## 3. S1 합성 데이터셋 확인 (낮 커밋 산출물 검증)
`data/episodes_s1/meta/info.json` (이번 세션 실측):
- **100 episodes / 7,231 frames** (프롬프트 W2 항목과 일치).
- 카메라 = `observation.images.top` + `observation.images.closeup` (실기 정렬 계약).
- LeRobot v3 포맷.

## 4. W3 ACT 학습 인에이블러 — `scripts/train_act.py` (미커밋 → 커밋)
낮 세션이 남긴 surgical 3필드 변경. 기본값 불변(하위호환), env 오버라이드만 추가:
- `dataset_repo_id` ← `COP_DATASET_REPO_ID` (S1 = `local/pcb_reset_sim`).
- `camera_keys` ← `COP_CAMERA_KEYS` 콤마구분 (S1 = `top,closeup`, 기본 `top` 유지).

이유: W3(8/19~) ACT 학습이 `episodes_s1`(top+closeup 2대, 6dof state/action)을
읽으려면 train_act 가 카메라 2대 + 다른 repo_id 를 받아야 한다. floor/cl 파이프라인
(단일 top, `local/cop-pickplace`)은 env 미지정 시 기존 그대로 동작.

검증: `ast.parse` OK. 기본값 미지정 경로 = 종전과 동일 문자열 → 드라이버 파이프라인 불변.

## 5. 다음 단계 연결
- Phase 3 W2 잔여: `omen lerobot 0.6.1 로드 스모크` — 실기 담당자 협업(외부 의존).
- Phase 3 W3 (8/19~): 이 인에이블러로 `episodes_s1` ACT 학습
  (obs = top+closeup+state6, 실기 하이퍼 chunk 100/batch 8) → LED 자동채점 rollout.
- Phase 2 잔여 2건(zero-shot 실기 = W4 핸드오프 이관 / full-epoch 04:04 killer)은
  외부 의존 대기 유지.
