# Phase 2 W2 — floor 배치다양성 재학습 4차: FD 누수 근본강화(RLIMIT_NOFILE) + 재시작 run

> 2026-07-11 (토요일) · 야간 sim 에이전트 v3.2
> 상위: [PHASE_ROADMAP.md](./PHASE_ROADMAP.md) Phase 2 W2 (Sim2Real, 배치 다양성 sim 트랙)
> 어제: [2026-07-10_phase2-w2-floor-retrain-fdfix-run.md](./2026-07-10_phase2-w2-floor-retrain-fdfix-run.md)

## 한 줄 요약
어제 FD-fix(`persistent_workers`) 발효 run(pid 39732)은 crash 지점을 **~epoch 49→59 로 밀었으나
100epoch 완주엔 실패**(epoch 59에서 이상종료) → 드라이버가 새 run(pid 56445) 재시작. 원인을
**크론 셸이 물려준 낮은 `RLIMIT_NOFILE` 소프트 한도**로 좁히고, **학습 프로세스가 자기 FD 한도를
하드 한도(무제한)까지 스스로 올리는 근본 fix** 를 [자가치유]로 추가(다음 run 부터 발효).

## 결정론적 드라이버 결과 (재실행 없음 — 드라이버 담당)
```
STAGE=학습시작  (episodes_floor 50ep 로 ACT 재학습, 100epoch → checkpoints/act_floor)
[start_act_train] 시작 pid=56445 log=logs/act_train.log args=--epochs 100 --no-resume
(shutdown 시 resource_tracker: 21 leaked semaphore objects 경고 — 직전 run 잔재)
```

## 어제 run(pid 39732)에 무슨 일이 있었나 — 증거
| 항목 | 값 | 해석 |
|---|---|---|
| `act_train_metrics.jsonl` 마지막 | **epoch 59** (loss 0.0123, ts 04:02) | 04:02에 metrics 기록 중단 |
| `checkpoints/act_floor/epoch_0059/model.safetensors` mtime | **7/11 04:02:48** | epoch 59까지 저장 |
| `epoch_0069`+ 존재 여부 | **없음** | epoch 59~68 사이 이상종료 |
| 직전 crash 지점 (pid 21661, fix 미적용) | ~epoch 49 (`epoch_0049` 7/9 03:45) | fix 로 **+10 epoch** 전진 |

→ `persistent_workers` fix 는 **효과는 있었으나 부분적**: 워커 재spawn 은 막았지만 누수를
완전 제거하진 못해 crash 지점만 뒤로 밀렸다(49→59). 100epoch 문턱은 여전히 못 넘음.

## 근본원인 재규명 — 한도(ceiling)의 문제였다
- 현 인터랙티브 셸 `RLIMIT_NOFILE` = `(1048576, unlimited)` 지만, **크론 셸은 훨씬 낮은 소프트
  한도(macOS 기본 256)를 물려준다**(7/9 로그가 이미 "낮은 ulimit -n" 으로 지목).
- persistent_workers 로도 epoch 당 소량 FD/세마포어가 누적(드라이버 출력의 "21 leaked semaphore"
  경고가 방증) → **256 / ~4 per-epoch ≈ 64 epoch** 후 `OSError [Errno 24] Too many open files`.
  → crash ~59 와 정합. 비-persistent(워커 4개 매 epoch 재spawn=누수 빠름)는 ~49 와 정합.
- ⇒ 진짜 벽은 **누수 속도**가 아니라 **프로세스가 물려받은 낮은 FD 천장**. 천장을 올리면
  누수 속도와 무관하게 완주 가능.

## [자가치유] RLIMIT_NOFILE 근본강화
`scripts/train_act.py` `main()` 진입 즉시 `_raise_fd_limit()` 호출 — 학습 프로세스가 **부모(크론)
셸과 무관하게 자기 소프트 한도를 하드 한도까지** 올린다. surgical(헬퍼 1개 + main 첫 줄 1개 +
결과 JSON `env.fd_limit_raised` 관측 필드), 학습 로직 무변경.

```python
def _raise_fd_limit():
    import resource
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    if soft >= hard: return None
    resource.setrlimit(resource.RLIMIT_NOFILE, (hard, hard))
    return (soft, hard)
```

### 검증 (비파괴, .venv)
- `ast.parse` OK.
- **시뮬 크론 한도 재현**: 프로세스 내 소프트를 256 으로 강제 → `_raise_fd_limit()` 호출 →
  `after: (9223372036854775807, ...)` = **소프트가 하드(무제한)로 상승** PASS.
- `train_act.py --dry-run` → `status: ok`, `env.fd_limit_raised: [1048576, ...]`(main 정상, 필드 노출).

### 발효 시점 (7/9→7/10 패턴 동일)
pid 56445 는 이 커밋 **이전** 디스크 코드를 이미 로드 → **이번 run 엔 미적용**(예측: 또 ~epoch 59
crash). 내일 드라이버가 이상종료 감지 후 재시작하면 **수정 코드 로드 → 256 천장 제거 → 100epoch
완주 기대**. 하드룰상 야간 에이전트는 실행중 학습을 kill/재시작하지 않는다.

## 무결성 격리 — 전수 불변 (baseline 무손상)
| 마커 | 값 | 상태 |
|---|---|---|
| `cop_dataset_target` | `data/episodes_floor` | 불변 |
| `cop_trained_on.marker` | `episodes_cl_dr:1783181837` | 불변(직전 승격값) |
| `cop_trained_on.marker.pending` | `episodes_floor:1783324998` | 대기·미승격 |
| `cop_measured.marker` | `episodes_cl_dr:1783346557` | 불변 |

- 운영 `rollout_summary.json` = **act_cl_dr · seed42 · 7/10=0.70 · median lift 50.2mm · measured 2026-07-07** → mtime 7/7 23:00 **불변**. (학습 미완 → pending 승격/측정 보류 = 설계대로)
- datasets `episodes_floor`·`episodes_cl`·`episodes_cl_dr` 각 **50ep/3350frame** 불변.
- ckpt `act`·`act_cl_dr`·`act_floor` 3자 분리. pid 56445 alive(epoch 1, loss 36→2.1 정상 수렴).

## 다음 단계 (드라이버 담당 — 재실행 금지)
- **pid 56445**: 미수정 코드라 ~epoch 59 재crash 예상 → 드라이버가 이상종료 감지 → **RLIMIT-fix
  적용 코드로 재시작 → 100epoch 완주** 기대(내일).
- **완주 시**: pending(`episodes_floor:...998`) 승격 → `act_floor/epoch_0099` 측정 →
  floor-trained rollout → 4-seed(42/7/123/2026) 공정추정으로 baseline(0.825)·DR-trained(0.800)
  대비 **배치 다양성이 성공률 천장을 올리는가 / 실패 배치가 이동·축소되는가**(7/7 W1 실증 처방).
- 실기 track: Orin/실기 SSH 외부의존 미수신 지속 감시(external-dependencies.md).
