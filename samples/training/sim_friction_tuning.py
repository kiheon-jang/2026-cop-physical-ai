#!/Users/markmini/Documents/dev/2026-cop-physical-ai/.venv/bin/python3

"""
sim_friction_tuning.py — SO-ARM100 frictionloss 튜닝 데모

frictionloss 튜닝 절차:
  1단계: 모든 값을 0으로 시작 → 진동/오버슈팅 확인
  2단계: 0.01~0.02씩 균일 증가 → 실제 로봇과 움직임 비교
  3단계: 관절별 세부 조정 → sim/real RMSE 최소화

실행:
  .venv/bin/python3 samples/training/sim_friction_tuning.py
"""

import mujoco
import mujoco.viewer
import numpy as np
import os

# ── 튜닝 파라미터 (이 딕셔너리만 수정하여 튜닝) ────────────────────────
# 현재: 모두 0 (베이스라인)
# 권장 시작값: 0.02~0.04 (균일), 이후 관절별 세부 조정
#
# 관절별 권장 최종 범위 (STS3215 서보 특성 기준):
#   shoulder_pan   0.03 ~ 0.06  (수평 회전, 베어링 마찰 주도)
#   shoulder_lift  0.06 ~ 0.10  (최대 하중, 중력 방향 동작)
#   elbow_flex     0.04 ~ 0.08  (중간 하중)
#   wrist_flex     0.02 ~ 0.05  (경량 하중)
#   wrist_roll     0.02 ~ 0.05  (경량, 그리퍼 하중만)
#   gripper        0.01 ~ 0.03  (최경량)
#
# 참고: XML sts3215 클래스 기본값 = 0.052 (모든 관절 동일)
FRICTIONLOSS = {
    "shoulder_pan":  0.0,
    "shoulder_lift": 0.0,
    "elbow_flex":    0.0,
    "wrist_flex":    0.0,
    "wrist_roll":    0.0,
    "gripper":       0.0,
}

SIM_DURATION = 8.0   # 총 시뮬 시간 (초)
AMPLITUDE    = 0.4   # 사인파 진폭 (rad)
FREQUENCY    = 0.5   # 사인파 주파수 (Hz)
# ──────────────────────────────────────────────────────────────────────────

MJCF_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../SO-ARM100/Simulation/SO101/so101_new_calib.xml",
    )
)


def apply_frictionloss(model: mujoco.MjModel, fl_map: dict) -> None:
    """model.dof_frictionloss 배열에 관절별 frictionloss를 직접 적용."""
    for joint_name, value in fl_map.items():
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
        if jid < 0:
            print(f"[경고] 관절 '{joint_name}' 없음 — 건너뜀")
            continue
        dof_adr = model.jnt_dofadr[jid]
        model.dof_frictionloss[dof_adr] = value


def log_state(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    """현재 관절 상태(위치·속도·frictionloss)를 콘솔에 출력."""
    print(f"\n[t={data.time:.2f}s]  {'관절':<18} {'위치(rad)':>10}  {'속도(rad/s)':>12}  frictionloss")
    print(f"          {'─'*58}")
    for name in FRICTIONLOSS:
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        if jid < 0:
            continue
        dof = model.jnt_dofadr[jid]
        pos = data.qpos[model.jnt_qposadr[jid]]
        vel = data.qvel[dof]
        fl  = model.dof_frictionloss[dof]
        print(f"          {name:<18} {pos:+8.4f}     {vel:+10.5f}    {fl:.4f}")


def main() -> None:
    if not os.path.exists(MJCF_PATH):
        print(f"오류: MJCF 파일 없음\n  경로: {MJCF_PATH}")
        return

    model = mujoco.MjModel.from_xml_path(MJCF_PATH)
    data  = mujoco.MjData(model)

    apply_frictionloss(model, FRICTIONLOSS)

    print("=" * 60)
    print("  SO-ARM100 frictionloss 튜닝 데모")
    print("=" * 60)
    print(f"  MJCF: {MJCF_PATH}")
    print(f"  시뮬 시간: {SIM_DURATION}s  진폭: {AMPLITUDE}rad  주파수: {FREQUENCY}Hz")
    print("\n  현재 frictionloss 설정:")
    for name, val in FRICTIONLOSS.items():
        print(f"    {name:<18} = {val}")
    print()

    # 액추에이터 순서 확인
    act_names = [model.actuator(i).name for i in range(model.nu)]
    print(f"  액추에이터 순서: {act_names}")
    print("\n  viewer 창에서 움직임을 확인하세요. (1초마다 상태 출력)")
    print("=" * 60)

    with mujoco.viewer.launch_passive(model, data) as viewer:
        viewer.sync()

        t0          = data.time
        next_log    = t0 + 1.0
        n_acts      = model.nu
        phase_step  = np.pi / max(n_acts, 1)

        while viewer.is_running() and (data.time - t0) < SIM_DURATION:
            t = data.time - t0

            # 각 액추에이터에 위상 오프셋을 달리한 사인파 목표 위치 전달
            for i in range(n_acts):
                phase = i * phase_step
                data.ctrl[i] = AMPLITUDE * np.sin(2 * np.pi * FREQUENCY * t + phase)

            mujoco.mj_step(model, data)
            viewer.sync()

            if data.time >= next_log:
                log_state(model, data)
                next_log += 1.0

    print("\n=== 시뮬 완료 ===")
    print()
    print("튜닝 가이드 요약:")
    print("  frictionloss 너무 낮음 → 빠른 오버슈팅, 진동, 실제보다 민첩함")
    print("  frictionloss 너무 높음 → 목표 위치 미도달, 응답 지연")
    print()
    print("  1) 0.0에서 시작 → 진동/오버슈팅 패턴 기록")
    print("  2) 0.02 단위로 증가 → 움직임이 실제와 유사해지는 값 탐색")
    print("  3) shoulder_lift 먼저 조정 (하중 영향 최대)")
    print("  4) sim_joint_angle_comparison_script.py로 실측 데이터와 RMSE 비교")
    print("  5) RMSE 최소 지점 = 최적 frictionloss")


if __name__ == "__main__":
    main()
