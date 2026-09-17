#!/Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv/bin/python
"""RS232 측정 민감도 도구 — 보유력 스윕 / 옛 씬 대조 (재학습·재수집·운영씬 수정 없음).

왜 필요한가
-----------
보유력(슬라이드 frictionloss)은 씬 XML 의 단일 추정 스칼라다. 근거인 Cinch M24308
데이터시트 접점 분리력 대역은 0.195~3.34 N/접점 → 9핀 환산 1.75~30 N (약 17배).
7.2 N 은 그 대역의 로그 중앙일 뿐이라, 단일 값으로 보고하면 "실제 커넥터가 더
뻑뻑하면?" 에 답할 수 없다. 대역 전체에 대한 곡선이 정직한 산출물이다.

render_act_rollout_rs232.py 를 고치지 않고 감싼다. 측정기가 main() 안에서
`from sim_rs232_unplug import Rs232UnplugTwin` 를 하므로, 호출 전에 클래스
__init__ 을 교체해두면 그대로 적용된다. 판정 임계(UNPLUG_FULL_M/PARTIAL_M),
시드, 배치 존, 롤아웃 수는 건드리지 않는다 — 측정기 인자 그대로 넘어간다.

사용
----
  # 보유력 스윕 1점 (seed42 ×10, 약 80초)
  .venv/bin/python3 scripts/sweep_rs232_sensitivity.py --friction 12.0 \
      --checkpoint checkpoints/_published_baseline_20260913/epoch_0041 \
      --out-dir /tmp/sweep_f12 --seeds 42 --rollouts 10

  # 옛 케이블 씬으로 대조 (기준 변경분 분리)
  .venv/bin/python3 scripts/sweep_rs232_sensitivity.py --scene /tmp/oldscene/rs232_unplug_scene.xml \
      --checkpoint checkpoints/_published_baseline_20260913/epoch_0041 \
      --out-dir /tmp/dec_oldscene --seeds 42 --rollouts 10

--out-dir 는 반드시 운영 디렉터리(research/simulation/inference_progress) 밖으로 줄 것.
그 안에 떨어지면 대시보드가 읽는 운영 수치를 덮어쓴다.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "samples" / "training"))

ap = argparse.ArgumentParser(add_help=False)
ap.add_argument("--friction", type=float, default=None,
                help="슬라이드 보유력 N 으로 덮어쓰기 (모델 로드 후, XML 불변)")
ap.add_argument("--scene", type=str, default=None,
                help="대체 씬 XML 경로 (예: git 에서 복원한 옛 케이블 씬)")
known, passthrough = ap.parse_known_args()

import sim_rs232_unplug as S  # noqa: E402

_orig_init = S.Rs232UnplugTwin.__init__


def _patched_init(self, scene_path: str = S.SCENE_PATH):
    _orig_init(self, known.scene or scene_path)
    if known.friction is not None:
        # dof_frictionloss 는 로드된 모델 배열 — XML 원본은 그대로다.
        self.model.dof_frictionloss[self.plug_dof] = known.friction


S.Rs232UnplugTwin.__init__ = _patched_init

import render_act_rollout_rs232 as M  # noqa: E402

if known.scene:
    print(f"[sweep] 씬 override = {known.scene}", flush=True)
if known.friction is not None:
    print(f"[sweep] 보유력 override = {known.friction} N (기본 7.2)", flush=True)

M.main(passthrough)
