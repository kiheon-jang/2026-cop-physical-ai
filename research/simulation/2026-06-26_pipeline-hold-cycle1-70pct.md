# 2026-06-26 — closed-loop 1사이클 완료/유지 (성공률 70%, 목표 90% 간극)

> Phase 1 - W4. 결정론적 드라이버 `scripts/cop_pipeline_advance.sh` 가 야간(01:00) 전진을 처리.
> 본 회차(sim-environment v3.2)는 드라이버 STAGE 결과를 검증·문서화·보고. **파이프라인 재실행 없음.**

## 드라이버 STAGE 결과 (2026-06-26 01:00)

```
════════ 🤖 CoP Physical AI 시뮬 파이프라인 (2026-06-26 01:00) ════════
STAGE=완료/유지  데이터 50ep · 최종 성공률=0.7 (목표 0.90)
  한 사이클 완료. 성공률 미달이면 COP_TARGET_EP 상향 또는 데이터 재수집(마커 삭제)으로 다음 사이클 트리거.
```

- **해석**: closed-loop 자동수집 1사이클(수집 50ep → ACT 100epoch → rollout 측정)은 6/25 02:17 학습완료 / 23:00 측정완료로 **완주**됨. 오늘 드라이버는 마커 정합(데이터·모델 서명 일치)을 확인 → **STAGE=완료/유지** (재학습/재측정 없이 상태 유지).
- 다음 사이클은 드라이버가 마커 리셋(`logs/cop_*.marker`) 또는 `COP_TARGET_EP` 상향 시에만 트리거. 이는 드라이버 담당이므로 본 회차에서 수동 트리거하지 않음.

## 산출물 디스크 검증

| 항목 | 값 | 출처 |
|---|---|---|
| 수집 데이터 | 50 ep / 3350 frame / 30fps / so101 | `data/episodes_cl/meta/info.json` |
| 학습 체크포인트 | `checkpoints/act/epoch_0099/model.safetensors` mtime **2026-06-25 02:17** (closed-loop 신선) | stat |
| 모델 사본 | `models/act_phase1.pt` 335MB | ls |
| rollout 측정 | 10 rollout 중 **7 성공 = 0.70**, median lift **43.7mm**, threshold 40mm, scene_grasp_pads, cpu, wall 13.6s | `research/simulation/inference_progress/rollout_summary.json` (mtime 6/25 23:00) |
| 측정 마커 | `cop_measured.marker` = 1782134830 (모델 서명 일치) | logs |

- 실패 3건(rollout 2/5/8) 전부 `max_lift ≤ 6.9mm` (그립 미성립). 성공 7건은 lift 43.7~45.6mm 로 안정적.

## 환경 무결성 재검증 (오늘 실행)

드라이버가 만든 산출물 위에서 sim 환경이 오늘도 정상 가동되는지 확인 (본 데이터 미손상, 임시경로 사용):

- **mujoco import**: `mujoco 3.8.0` (.venv, Apple Silicon) ✓
- **closed-loop 수집기 스모크** (`sim_data_collector.py --episodes 2`, 임시 root):
  성공 **2/2** (yield 100%), lift 43.2mm, grasp 재시도 1회 → closed-loop expert + scene_grasp_pads 정상 ✓
- **grasp 씬**: `SO-ARM100/Simulation/SO101/scene_grasp_pads.xml` 존재 ✓

## 검증 방법

- `rollout_summary.json` 직접 파싱 + `cop_measured.marker` 모델 서명 대조 → 측정 정합 확인.
- 체크포인트 신선도는 **파일 mtime**(02:17) 기준 — 디렉터리 mtime(save_pretrained 미갱신 특성)은 무시.
- 환경 무결성은 임시 root 스모크 2ep 실행으로 end-to-end 확인.

## 다음 단계 연결

- **Phase 1 W4 사실상 종료**: 남은 dated 항목은 PHASE_ROADMAP L168 "학습 모델 Orin Nano 배포"뿐 →
  외부 의존(장기헌 SSH, `external-dependencies.md`) 미수신으로 이연.
- **성공률 간극(70% < 90%)**: ACT 모방격차 + sim 데이터 50ep 한계. 90%+ 는 Sim2Real 진입 조건 →
  자연스러운 후속 = 데이터 증대(50→200ep)/씬 다양화. 7월 Phase 2(Sim2Real) 진입 전 향상 과제.
- 다음 사이클은 드라이버 마커 리셋/타깃 상향 시 자동 전진.
