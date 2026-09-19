"""Phase 4 W1 — 3단계 RS232(HHT) 케이블 분리 closed-loop expert + LeRobot 수집기 (실기 정렬).

sim_rs232_unplug.Rs232UnplugTwin 위에서 동작. 구조·규약은 S1 sim_pcb_reset_collector.py 와 동일:
  - observation.images.top / observation.images.closeup (640×480@30, video)
  - observation.state / action = 6dof pos
  - task = "unplug the rs232 cable"
  - 성공 판정 = 플러그 슬라이드 변위 FULL latch (UNPLUG_FULL_M, 트윈 모듈 상수 공유).
    expert 시연 채택은 더 엄격: 핀치 확인 + FULL latch + 변위 ≥ 1.5×FULL.

존 근단(후드 r ≲ 0.117m): 수직(탑다운) 측면 핀치는 shoulder 링크와 moving_jaw/gripper 가 관통 (200-seed 계획 스캔
34/200, 2026-09-11) → 그리퍼 축을 팔 평면 안에서 바깥으로 기울인 파지(TILTS_DEG, wrist_flex 로 손목을 shoulder 에서 띄움)를
θ=0 해에서 continuation 으로 탐색. 기울기는 팔 평면(shoulder_lift 축의 수직면)에 묶이므로 보드 y 와 방사 방향이 어긋난
배치에선 jaw 개폐축이 보드 y 에서 벗어난다(ALIGN_MAX_DEG 로 제한). 그래도 무관통·핀치 가능한 자세가 없으면 실행하지 않고
사유를 남긴다: unreachable(파지 자세 불가 또는 FULL 이전에 당김 경로 관통) / margin_blocked(FULL 까지는 무관통이나
expert 채택 여유 PULL_REQ 이전에 관통) — 둘 다 max_clear_pull_mm 기록.

Expert:
  - GRASP_LOCAL: 파지 중심 (gripper 로컬) — 후드 핀치 시 고정 jaw·가동 jaw 접촉점의 중점 실측 캘리브.
    (S1 교훈: TCP/gripperframe 이 아니라 실제로 닿는 jaw 접촉점 기준으로 겨냥)
  - 후드 관측 → 무관통 파지 자세 계획(plan_grasp: 기울기 × 축방향 파지점 이동 × wrist roll ±π, 닫힘 sweep 관통·
    기하 핀치(양 jaw↔후드 거리)·당김 경로 1mm 간격 관통 검사)
    → pan 정렬 → 후드 위 60mm 경유 → 단계 하강(매 단계 IK 재계산, 고정 jaw 측면 여유 → 마지막에 0)
    → jaw 조임 → 핀치 확인(양 jaw 후드 접촉) → 커넥터 축(팔 방향)으로 2mm 씩 당김(매 단계 IK) 변위 ≥ 1.5×FULL 까지
    → latch 확인 → jaw 열고 후퇴. 실패 시 후드 재관측 후 재계획·재파지(최대 MAX_ATTEMPTS_PER_EP).
  - 수집 저장 정책: 기본은 1차 시도 성공 에피소드만 저장(--allow-retry 로 재시도 성공 포함). MAX_FRAMES 초과는 폐기. 1차 실패 구간에는 jaw 가
    포트에 박히거나 플러그를 밀어넣는 프레임이 들어가므로 시연으로 쓰지 않는다.

환경 수정 금지 원칙: 커넥터 치수·보유력·판정 임계·존은 트윈 그대로.
"""
import os
import json
import numpy as np
import mujoco

from sim_rs232_unplug import Rs232UnplugTwin, CAM_W, CAM_H, FPS, TASK_LABEL, UNPLUG_FULL_M
from sim_pcb_reset_collector import PressExpert, JOINT_NAMES  # S1 IK·record 훅 재사용

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASET_ROOT = os.path.join(BASE, "data", "episodes_rs232")
DATASET_REPO_ID = "local/rs232_unplug_sim"

# 파지 중심 (gripper 로컬) — 핀치 접촉점 실측 (2026-09-11, 6배치): 고정 jaw x=-4.2mm, 가동 jaw x=+26.8mm
# (후드 폭 31mm 와 일치) → 중점 x=11.3, y≈-0.3; z 는 후드 중심 높이 (jaw 끝이 후드 상면 아래 ~10mm 물림)
GRASP_LOCAL = np.array([0.0113, -0.0003, -0.1021])
WAYPOINT_Z = 0.060
DESCENT_Z = (0.030, 0.010, 0.0)       # 후드 중심 대비 단계 하강 높이
SIDE_CLEAR = 0.002                    # 하강 중 고정 jaw ↔ 후드 측면 여유 (마지막 단계에서 0)
G_OPEN = 0.8                          # 열림: jaw 끝이 후드 상면보다 높게 들림 (-88.9mm > -94.4mm)
G_CLOSE = -0.15                       # 후드 접촉각 0.25 에서 0.4rad 더 조임
PULL_STEP = 0.002
PULL_MAX = 0.020
PULL_DISP = 1.5 * UNPLUG_FULL_M       # 1.5×FULL 이상 빼고 멈춤
PULL_REQ = PULL_DISP + 0.002          # 계획: 이 거리까지 당김 경로가 무관통이어야 채택 (1mm 간격 검사)
G_CONTACT = 0.25                      # jaw 가 후드 측면에 닿는 각 (실측)
MAX_ATTEMPTS_PER_EP = 2
# 축방향 파지점 이동 후보 (보드 쪽 +). 9mm 는 제거: jaw↔포트 여유 0~2.5mm 라 기하 핀치는 성립해도 실행에서
# grasp_miss (강제 실행 1004·1015, seed 1170 1차 시도 moving_jaw↔rs232_port -0.8mm, 검증 2026-09-11)
GRASP_SHIFTS = (0.0, 0.005)
TILTS_DEG = (0, 5, 10, 15, 20, 25, 30)  # 그리퍼 축 기울기 후보 (팔 평면, 손목이 바깥쪽). 0 이 우선 — 기존 수직 파지 불변
ALIGN_MAX_DEG = 15.0                  # jaw 개폐축 ↔ 보드 y 최대 어긋남
PINCH_GEOM_TOL = 1e-3                 # 계획 자세(접촉각)에서 고정·가동 jaw ↔ 후드 거리 상한
KIN_PEN_TOL = 5e-4                    # 계획 자세 팔 관통 허용 (self-check [6] 과 동일)
# --- 2026-09-11 공통 핵심 (원인 수정 4 + SEAT + 한계 인지 IK + 충돌 검사 + 계획 후 실행) ---
SWEEP_TOL = 0.0                       # pan sweep·이동 경로 팔 접촉(플러그·포트·PCB·base·자기) 허용 0: dist<0 이면 거부
#                                       (0.1mm 허용 시 -0.03mm 스침이 shoulder↔port 212N 을 냄, 검증 HOLD 2026-09-11)
ARM_ENV_F_MAX = 1.0                   # 실행 중 비그리퍼 팔 링크↔환경 법선력 상한 [N]: 넘으면 에피소드 불합격(채택 기준, 저장 안 함)
ROLL_MARGIN = np.radians(4.0)         # wrist_roll 계획 한계 여유: 경유점 이동(최대 ~160°/300스텝) 끝 관성 overshoot 가 명령 대비
#                                       최대 2.83° (DEV 20189·21347, 여유 2° 에서 한계 0.83° 초과) → 4° 에서 초과 0 (DEV 240)
SEAT_STEP = 0.00025                   # SEAT: 고정 jaw 비접촉 시 gripper +x 이동 단위 (최대 SEAT_N 회, 각 20스텝)
SEAT_N = 8
MAX_FRAMES = 200                      # 수집: 이 프레임 초과 시연은 폐기
# --- 계획별 최소 개방각 (근단 jaw↔shoulder·후드 여유) ---
G_OPENS = (0.8, 0.7, 0.6, 0.5)        # 계획별 열림각 후보 (큰 값 우선, 하강·닫힘 무관통인 최대값). 0.5 ≈ 접촉각 0.25 + 후드 31mm·여유 2mm


class UnplugExpert(PressExpert):
    """closed-loop 후드 파지-당김. PressExpert 의 _phys_step(record 훅) 재사용. IK 는 관절 한계 투영(_ik_lim/_ik)."""

    def __init__(self, twin: Rs232UnplugTwin):
        super().__init__(twin)
        m = twin.model
        self.HOOD = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "rs232_plug_hood")
        self.JAW_BID = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
        self.ARM_BODIES = {b for b in range(m.nbody) if m.body_rootid[b] == m.body_rootid[self.GBID]}
        self.J_LIFT = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, "shoulder_lift")
        coll = lambda b: [g for g in range(m.ngeom) if m.geom_bodyid[g] == b and (m.geom_contype[g] or m.geom_conaffinity[g])]
        self.G_STATIC, self.G_MOV = coll(self.GBID), coll(self.JAW_BID)
        self._LO = m.jnt_range[[m.dof_jntid[i] for i in self.DOF], 0].copy()   # 실기 관절 한계 (env 모델)
        self._HI = m.jnt_range[[m.dof_jntid[i] for i in self.DOF], 1].copy()
        self._LO[4] += ROLL_MARGIN; self._HI[4] -= ROLL_MARGIN
        self._th = 0.0   # 현재 계획의 그리퍼 기울기 [rad]
        self._F6 = np.zeros(6)
        self._ep_envF = 0.0

    # --- 관측 / 운동학 ---
    def _hood(self):
        d = self.t.data
        axis = d.xmat[self.t.plug_bid].reshape(3, 3) @ np.array([-1.0, 0, 0])   # 빠지는 방향(팔 쪽)
        return d.geom_xpos[self.HOOD].copy(), axis, d.xmat[self.t._pcb_bid].reshape(3, 3)[:, 1].copy()

    def _fk(self, q, qg, plug=None):
        d, di = self.t.data, self.d_ik
        di.qpos[:] = d.qpos
        di.qpos[self.QAD] = q
        di.qpos[5] = qg
        if plug is not None:                     # (3) 당김 경로 검사: 플러그 슬라이드 = 당긴 거리
            di.qpos[self.t._plug_qadr] = plug
        mujoco.mj_forward(self.t.model, di)
        R = di.xmat[self.GBID].reshape(3, 3).copy()
        return R, di.xpos[self.GBID] + R @ GRASP_LOCAL

    def _arm_pen(self, dd, grip_plug=True):
        """dd 자세에서 팔 geom 의 최소 접촉 dist [m] 와 그 쌍. (3) 플러그 접촉은 gripper/moving_jaw↔플러그만 제외
        (grip_plug=False 면 그것도 셈 — 하강 중 jaw 가 후드 상면에 걸리는지 검사)."""
        m = self.t.model
        worst, pair = 0.0, None
        for c in dd.contact[:dd.ncon]:
            b1, b2 = m.geom_bodyid[c.geom1], m.geom_bodyid[c.geom2]
            if not ({b1, b2} & self.ARM_BODIES):
                continue
            if grip_plug and self.t.plug_bid in (b1, b2) and {b1, b2} & {self.GBID, self.JAW_BID}:
                continue
            if c.dist < worst:
                bn = lambda b: mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, b)
                worst, pair = float(c.dist), (bn(b1), bn(b2))
        return worst, pair

    def _path_pen(self, qs, gs, n, grip_plug):
        """관절 공간 직선 경로 qs[i]→qs[i+1] (gripper gs[i]→gs[i+1], step_to 와 같은 선형 보간) 을 구간당 n 점 FK →
        팔 접촉 최소 dist 와 쌍. 팔↔팔·팔↔환경(플러그·포트·PCB·base_collision) 모두 셈."""
        worst, pair = 0.0, None
        for i in range(len(qs) - 1):
            for tt in np.linspace(0.0, 1.0, n)[(1 if i else 0):]:
                self._fk(qs[i] + (qs[i + 1] - qs[i]) * tt, gs[i] + (gs[i + 1] - gs[i]) * tt)
                w, pr = self._arm_pen(self.d_ik, grip_plug)
                if w < worst:
                    worst, pair = w, pr
        return worst, pair

    def _ik(self, target, seed, th):
        """GRASP_LOCAL 을 target 에. th=0 이면 그리퍼 z = 월드 수직(_ik_lim), th>0 이면 그리퍼 z 를 팔 평면
        (shoulder_lift 축에 수직인 연직면) 안에서 바깥쪽으로 th 기울인 방향에 맞춘다 (같은 DLS, 5 관절, 매 반복 한계 투영)."""
        if th == 0.0:
            return self._ik_lim(target, seed)
        m, di = self.t.model, self.d_ik
        q = np.clip(np.array(seed, float), self._LO, self._HI)
        for _ in range(1000):
            di.qpos[self.QAD] = q
            mujoco.mj_forward(m, di)
            R = di.xmat[self.GBID].reshape(3, 3)
            pt = di.xpos[self.GBID] + R @ GRASP_LOCAL
            rout = np.cross(di.xaxis[self.J_LIFT], [0.0, 0.0, 1.0])
            rout[2] = 0.0
            rout *= np.sign(rout @ target) / np.linalg.norm(rout)
            up = np.cos(th) * np.array([0.0, 0.0, 1.0]) + np.sin(th) * rout
            pe, re = target - pt, np.cross(R[:, 2], up)
            if np.linalg.norm(pe) < 5e-4 and np.linalg.norm(re) < 0.02:
                break
            jacp = np.zeros((3, m.nv)); jacr = np.zeros((3, m.nv))
            mujoco.mj_jac(m, di, jacp, jacr, pt, self.GBID)
            J = np.vstack([jacp[:, self.DOF], jacr[:, self.DOF]])
            dq = J.T @ np.linalg.solve(J @ J.T + 0.04 * np.eye(6), np.concatenate([pe, 0.7 * re]))
            q = np.clip(q + np.clip(dq, -0.2, 0.2), self._LO, self._HI)
        return q

    def _ik_lim(self, target, seed):
        """S1 ik_point 과 같은 DLS(그리퍼 z 수직) + 매 반복 관절 한계 투영."""
        m, di = self.t.model, self.d_ik
        q = np.clip(np.array(seed, float), self._LO, self._HI)
        UP = np.array([0., 0., 1.])
        for _ in range(700):
            di.qpos[self.QAD] = q
            mujoco.mj_forward(m, di)
            R = di.xmat[self.GBID].reshape(3, 3)
            pt = di.xpos[self.GBID] + R @ GRASP_LOCAL
            pe, re = target - pt, np.cross(R[:, 2], UP)
            if np.linalg.norm(pe) < 5e-4 and np.linalg.norm(re) < 0.02:
                break
            jacp = np.zeros((3, m.nv)); jacr = np.zeros((3, m.nv))
            mujoco.mj_jac(m, di, jacp, jacr, pt, self.GBID)
            J = np.vstack([jacp[:, self.DOF], jacr[:, self.DOF]])
            dq = J.T @ np.linalg.solve(J @ J.T + 0.04 * np.eye(6), np.concatenate([pe, 0.7 * re]))
            q = np.clip(q + np.clip(dq, -0.2, 0.2), self._LO, self._HI)
        return q

    def _in_lim(self, q):
        return bool(np.all((q >= self._LO - 1e-6) & (q <= self._HI + 1e-6)))

    def _hood_gap(self, geoms):
        m = self.t.model
        return min(mujoco.mj_geomDistance(m, self.d_ik, g, self.HOOD, 0.05, None) for g in geoms)

    def plan_grasp(self, c, axis, y_pcb):
        """무관통·핀치 가능 파지 자세 + 실행 경로 탐색 (실행 전에 전부 검사). 후보 = 기울기(TILTS_DEG, 이전 기울기 해에서
        continuation) × 축방향 파지점 이동(GRASP_SHIFTS) × 가동 jaw 쪽(±y_pcb).
        IK 시드는 한계 투영.
        각 후보: IK → jaw 개폐축(gripper x)을 ±y_pcb 로 roll 정렬 → IK 재계산 후 검사
          (1) IK 오차 < 2mm, jaw 축 어긋남 ≤ ALIGN_MAX_DEG, q 가 관절 한계 안
          (2) 열림각 G_OPENS 중 큰 값부터: 열림→접촉각 sweep + 완전 닫힘 관통 없음(gripper/jaw↔플러그만 허용)
              + 하강 경로(현재 gripper→열림, 경유 60mm→30→10→0(측면 여유)→최종) 관통 없음(jaw↔플러그도 셈) — 통과한 최대 열림각 채택
          (3) 기하 핀치: 접촉각에서 고정 jaw·가동 jaw 모두 후드와 거리 ≤ PINCH_GEOM_TOL
          (4) (2) pan sweep(현재 명령→계획 pan, 61점) + 경유점 이동(21점) 팔 관통 < SWEEP_TOL
          (5) 당김 경로(닫힘, 1mm 간격, 매 점 IK·플러그 슬라이드 이동, IK 오차 < 2mm) 무관통 최대 거리 max_clear ≥ PULL_REQ
        (1)~(4) = grasp_ok, (5) 까지 = feasible. 첫 feasible 후보 반환(가동 jaw -y_pcb 쪽 먼저). 없으면 grasp_ok 중 max_clear 최대
        (fail = margin_blocked if max_clear ≥ FULL else unreachable), grasp_ok 도 없으면 관통 최소 후보(fail=unreachable).
        반환 dict(q, R, target, shift, tilt, align_deg, ik_err, pen, pair, pinch_gap, max_clear, feasible, fail, jaw_side,
        g_open, path=[경유, 하강3, 최종])."""
        d = self.t.data
        start_q, start_g = d.ctrl[:5].copy(), float(d.ctrl[5])
        best_ok = best_any = None
        cont = {}
        for th_deg in TILTS_DEG:
            th = np.radians(th_deg)
            for shift in GRASP_SHIFTS:
                tgt = c - axis * shift
                out = []
                for sgn in (1.0, -1.0):
                    xref = sgn * y_pcb
                    if (shift, sgn) in cont:                   # 이전 기울기 해에서 continuation
                        q = self._ik(tgt, cont[(shift, sgn)], th)
                    else:
                        q0 = np.array([d.qpos[a] for a in self.QAD])
                        q0[0] = np.arctan2(tgt[1], tgt[0])
                        q = self._ik(tgt, q0, 0.0)
                    for k in range(3):
                        R = self._fk(q, G_OPEN)[0]
                        dr = np.arctan2(np.cross(R[:, 0], xref) @ R[:, 2], R[:, 0] @ xref)
                        q[4] = (q[4] + dr + np.pi) % (2 * np.pi) - np.pi
                        q = self._ik(tgt, q, th)
                    cont[(shift, sgn)] = q.copy()
                    out.append(self._eval_cand(q, tgt, axis, y_pcb, th, shift, start_q, start_g))
                for cand in sorted(out, key=lambda x: x["jaw_side"]):   # 가동 jaw 가 -y_pcb 쪽인 해 먼저
                    if cand["feasible"]:
                        return dict(cand, fail=None)
                    if cand["grasp_ok"]:
                        if best_ok is None or cand["max_clear"] > best_ok["max_clear"]:
                            best_ok = cand
                    elif best_any is None or cand["pen"] > best_any["pen"]:
                        best_any = cand
        if best_ok is not None:
            return dict(best_ok, fail="margin_blocked" if best_ok["max_clear"] >= UNPLUG_FULL_M else "unreachable")
        return dict(best_any, fail="unreachable")

    def _eval_cand(self, q, tgt, axis, y_pcb, th, shift, start_q, start_g):
        R, p = self._fk(q, G_OPEN)
        err = float(np.linalg.norm(p - tgt))
        align = float(np.degrees(np.arccos(min(1.0, abs(R[:, 0] @ y_pcb)))))
        cand = dict(q=q, R=R, target=tgt, shift=shift, tilt=th, align_deg=align, ik_err=err, pen=-1.0, pair=None,
                    pinch_gap=1.0, max_clear=0.0, grasp_ok=False, feasible=False, jaw_side=float(R[:, 0] @ y_pcb),
                    g_open=None, path=None, block="ik_align_limit")
        if not (err < 2e-3 and align <= ALIGN_MAX_DEG and self._in_lim(q)):
            return cand
        self._fk(q, G_CONTACT)
        cand["pinch_gap"] = gap = max(self._hood_gap(self.G_STATIC), self._hood_gap(self.G_MOV))
        if gap > PINCH_GEOM_TOL:
            cand["block"] = "pinch_gap"
            return cand
        # 실행 경로 (run_episode 가 그대로 씀): 경유 → 하강 3단(측면 여유) → 최종. 시드 = 직전 명령 (원인 (1))
        side = -SIDE_CLEAR * R[:, 0]              # 고정 jaw(gripper -x 쪽)를 후드 측면에서 띄움
        path = [self._ik(tgt + side + [0, 0, WAYPOINT_Z], q, th)]
        for dz in DESCENT_Z:
            path.append(self._ik(tgt + side + [0, 0, dz], path[-1], th))
        path.append(self._ik(tgt, path[-1], th))
        # 경유·하강 중간점은 wrist_flex 한계(파지 자세가 이미 87~90°)로 정확히 못 가는 배치가 많아(경유 오차 12~21mm) 통과점으로 두고,
        # 도달 오차는 최종 자세만 검사한다. 충돌은 한계 투영된 실제 경로(FK)로 아래에서 검사.
        if np.linalg.norm(self._fk(path[-1], G_OPEN)[1] - tgt) > 2e-3:
            cand["block"] = "path_ik_limit"
            return cand
        pen, pair = -1.0, None
        for g_open in G_OPENS:                    # 무관통인 최대 열림각
            w, pr = 0.0, None
            for g in list(np.linspace(g_open, G_CONTACT, 6)) + [G_CLOSE]:
                self._fk(path[-1], g)
                w2, pr2 = self._arm_pen(self.d_ik)
                if w2 < w:
                    w, pr = w2, pr2
            if w >= -KIN_PEN_TOL:
                w2, pr2 = self._path_pen([path[0]] + path, [start_g] + [g_open] * len(path), 6, grip_plug=False)
                if w2 < w:
                    w, pr = w2, pr2
            if w > pen:
                pen, pair = w, pr
            if w >= -KIN_PEN_TOL:
                cand["g_open"] = g_open
                break
        cand.update(pen=pen, pair=pair, path=path)
        if cand["g_open"] is None:
            cand["block"] = "grasp_or_descent_pen"
            return cand
        qpan = start_q.copy(); qpan[0] = q[0]     # (2) pan sweep + 경유점 이동
        w, pr = self._path_pen([start_q, qpan], [start_g, start_g], 61, grip_plug=False)
        w2, pr2 = self._path_pen([qpan, path[0]], [start_g, start_g], 21, grip_plug=False)
        if min(w, w2) < -SWEEP_TOL:
            cand.update(pen=min(w, w2), pair=pr if w <= w2 else pr2, block="pan_sweep_or_transit")
            return cand
        cand.update(grasp_ok=True, block=None)
        clear, qp = 0.0, path[-1]                 # 당김 경로: 1mm 간격, 첫 관통(또는 한계로 IK 불가) 직전까지가 무관통 최대 거리
        for dist in list(np.arange(0.001, PULL_REQ, 0.001)) + [PULL_REQ]:
            qp = self._ik(tgt + axis * dist, qp, th)
            _, pp = self._fk(qp, G_CONTACT, plug=float(dist))
            w, pr = self._arm_pen(self.d_ik)
            if w < -KIN_PEN_TOL or np.linalg.norm(pp - (tgt + axis * dist)) > 2e-3:
                cand["pair"] = pr if w < -KIN_PEN_TOL else ("pull_ik_limit",)
                break
            clear = float(dist)
        cand.update(max_clear=clear, feasible=clear >= PULL_REQ - 1e-9)
        return cand

    def step_to(self, q_arm, n, g=None):
        d = self.t.data
        cur, g0 = d.ctrl[:5].copy(), float(d.ctrl[5])
        g = g0 if g is None else g
        for s in range(n):
            tt = (s + 1) / n
            d.ctrl[:5] = cur + (q_arm - cur) * tt
            d.ctrl[5] = g0 + (g - g0) * tt
            self._phys_step()
            self._arm_env_force()

    def _arm_env_force(self):
        """비그리퍼 팔 링크 ↔ 환경 접촉 법선력 에피소드 최대 갱신 (계획 모델과 동역학 차이로 생긴 충돌 시연 거르기)."""
        m, d = self.t.model, self.t.data
        for i in range(d.ncon):
            c = d.contact[i]
            arm = {int(m.geom_bodyid[c.geom1]), int(m.geom_bodyid[c.geom2])}
            if len(arm) == 2 and len(arm & self.ARM_BODIES) == 1 and not arm & {self.GBID, self.JAW_BID}:
                mujoco.mj_contactForce(m, d, i, self._F6)
                self._ep_envF = max(self._ep_envF, float(self._F6[0]))

    def _tcp(self):
        d = self.t.data
        return d.xpos[self.GBID] + d.xmat[self.GBID].reshape(3, 3) @ GRASP_LOCAL

    def _q(self):
        return [self.t.data.qpos[a] for a in self.QAD]

    def _hood_contacts(self):
        m, d = self.t.model, self.t.data
        static = jaw = False
        for c in d.contact[:d.ncon]:
            if self.HOOD in (c.geom1, c.geom2):
                b = m.geom_bodyid[c.geom2 if c.geom1 == self.HOOD else c.geom1]
                jaw |= b == self.JAW_BID
                static |= b == self.GBID
        return static, jaw

    # --- 에피소드 ---
    def _stage(self, q_arm, n, g=None):
        """step_to + 단계 끝 팔 관통 기록 (gripper/jaw↔플러그 제외)."""
        self.step_to(q_arm, n, g)
        w, pair = self._arm_pen(self.t.data)
        if w < self._ep_pen[0]:
            self._ep_pen = (w, pair)

    def run_episode(self):
        """홈에서 분리 1회. 성공 = 핀치 확인 + FULL latch + 변위 ≥ 1.5×FULL.
        반환 dict(success, attempts, reason(마지막 시도 사유), history(시도별 진단)).
        사유: unreachable(파지 자세·경로 불가 또는 FULL 이전 당김 경로 관통, 미실행) / margin_blocked(FULL 까지 무관통,
              PULL_REQ 이전 관통, 미실행) / approach_blocked / grasp_miss / grasp_slip / jam /
              short_pull / threshold_not_reached.
        순서: 관측 → plan_grasp(파지·열림각·하강·pan sweep·이동·당김 검사) → feasible 일 때만 pan → 경유 → 하강 → 최종
              → 닫힘 → SEAT → 핀치 확인 → 당김 → 놓기·후퇴. (4) 불가 배치에서는 팔을 움직이지 않는다.
        파지 확인(고정·가동 jaw 모두 후드 접촉) 없이는 당기지 않는다 — 한쪽 jaw 로 누르고 끄는 비핀치 분리는
        실기 재현 위험이 커서 시연으로 쓰지 않는다."""
        t, d = self.t, self.t.data
        history = []
        reason = None
        self._ep_envF = 0.0
        mujoco.mj_resetData(self.t.model, self.d_ik)   # IK 작업 MjData 의 이전 에피소드 잔여 상태 제거 → 실행 순서 무관 결정론 (검증 2026-09-11)
        for attempt in range(MAX_ATTEMPTS_PER_EP):
            c, axis, y_pcb = self._hood()              # 관측 (재시도 시 재관측, closed-loop)
            plan = self.plan_grasp(c, axis, y_pcb)
            tgt, self._th = plan["target"], plan["tilt"]
            att = {"attempt": attempt + 1, "plan_feasible": plan["feasible"], "plan_ik_err_mm": round(plan["ik_err"] * 1e3, 2),
                   "plan_pen_mm": round(plan["pen"] * 1e3, 2), "plan_pen_pair": plan["pair"], "plan_block": plan["block"],
                   "grasp_shift_mm": round(plan["shift"] * 1e3, 1), "tilt_deg": round(float(np.degrees(plan["tilt"])), 1),
                   "align_deg": round(plan["align_deg"], 1), "pinch_gap_mm": round(plan["pinch_gap"] * 1e3, 2),
                   "max_clear_pull_mm": round(plan["max_clear"] * 1e3, 1), "g_open": plan["g_open"],
                   "moving_jaw_side": "-y" if plan["jaw_side"] < 0 else "+y"}
            history.append(att)
            self._ep_pen = (0.0, None)
            if not plan["feasible"]:
                # 무관통·핀치 가능한 파지+경로+당김 자세가 없음 → 실행하지 않음 (pan 도 돌리지 않음)
                att["reason"] = reason = plan["fail"]
                break
            qw, *desc, qc = plan["path"]
            qpan = d.ctrl[:5].copy(); qpan[0] = plan["q"][0]
            self._stage(qpan, 200)
            self._stage(qw, 300)
            self._stage(qw, 120, g=plan["g_open"])
            for qd in desc:
                self._stage(qd, 150)
            self._stage(qc, 100)
            approach_err = float(np.linalg.norm(self._tcp() - tgt))
            self._stage(qc, 250, g=G_CLOSE)
            self._stage(qc, 100)
            seat = 0
            if self._hood_contacts() == (False, True):  # SEAT: 가동 jaw 만 닿음 → 고정 jaw 쪽(gripper +x)으로 조금씩
                Rg = d.xmat[self.GBID].reshape(3, 3)[:, 0].copy()
                for seat in range(1, SEAT_N + 1):
                    qc = self._ik(tgt + Rg * SEAT_STEP * seat, qc, self._th)
                    self._stage(qc, 20)
                    if self._hood_contacts()[0]:
                        break
            pinch = all(self._hood_contacts())
            att.update(approach_err_mm=round(approach_err * 1e3, 2), seat_steps=seat, pinch=pinch,
                       disp_at_pinch_mm=round(t.plug_displacement() * 1e3, 3))

            if pinch:   # 당김: 커넥터 축으로 2mm 씩, 매 단계 IK 재계산(시드 = 실제 qpos), 핀치 풀리면 중단
                tcp0 = self._tcp()
                rel0 = (tcp0 - d.xpos[t.plug_bid]) @ axis
                disp0 = t.plug_displacement()
                goal, lost = tgt, False
                for k in range(1, int(round(PULL_MAX / PULL_STEP)) + 1):
                    goal = tgt + axis * k * PULL_STEP
                    qc = self._ik(goal, self._q(), self._th)
                    self._stage(qc, 150)
                    if t.plug_displacement() >= PULL_DISP:
                        break
                    if not all(self._hood_contacts()):
                        lost = True
                        break
                trav = float((self._tcp() - tcp0) @ axis)
                slip = float((self._tcp() - d.xpos[t.plug_bid]) @ axis - rel0)
                att.update(pull_disp_mm=round((t.plug_displacement() - disp0) * 1e3, 2),
                            tcp_travel_mm=round(trav * 1e3, 2), slip_mm=round(slip * 1e3, 2),
                            track_err_mm=round(float(np.linalg.norm(goal - self._tcp())) * 1e3, 2), pinch_lost=lost)

            # 놓고 후퇴 (종단 상태: jaw 열림, 후드 위)
            self._stage(np.clip(self._q(), self._LO, self._HI), 150, g=plan["g_open"])   # 실제 qpos 가 한계를 살짝 넘을 수 있어 명령은 투영
            up = self._ik(self._tcp() + [0, 0, WAYPOINT_Z], self._q(), self._th)
            self._stage(up, 250)
            att.update(final_disp_mm=round(t.plug_displacement() * 1e3, 2),
                        episode_arm_pen_mm=round(self._ep_pen[0] * 1e3, 2), episode_arm_pen_pair=self._ep_pen[1],
                        arm_env_force_N=round(self._ep_envF, 1))
            if pinch and t.unplugged_full() and t.plug_displacement() >= PULL_DISP and self._ep_envF <= ARM_ENV_F_MAX:
                att["reason"] = "ok"
                return {"success": True, "attempts": attempt + 1, "reason": "ok", "history": history}

            if self._ep_envF > ARM_ENV_F_MAX:
                reason = "arm_env_contact"         # 비그리퍼 링크가 환경을 침 (에피소드 전체 기준, 재시도 성공도 불합격)
            elif approach_err > 3e-3:
                reason = "approach_blocked"
            elif not pinch:
                reason = "grasp_miss"
            elif att["pinch_lost"] or att["slip_mm"] > 0.5 * max(att["tcp_travel_mm"], 1.0):
                reason = "grasp_slip"
            elif att["track_err_mm"] > 5.0:
                reason = "jam"
            elif t.unplugged_full():
                reason = "short_pull"              # FULL latch 는 됐으나 1.5×FULL 미만
            else:
                reason = "threshold_not_reached"
            att["reason"] = reason
        return {"success": False, "attempts": len(history), "reason": reason, "history": history}


def expert_eval(seed0, count, out=None):
    twin = Rs232UnplugTwin()
    ex = UnplugExpert(twin)
    per_seed = []
    for s in range(seed0, seed0 + count):
        p = twin.reset(np.random.default_rng(s))
        r = ex.run_episode()
        row = {"seed": s, "success": r["success"], "reason": r["reason"], "attempts": r["attempts"],
               "pcb": {k: round(v, 4) for k, v in p.items() if k != "rejected"}, "history": r["history"]}
        per_seed.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    fails = {}
    for r in per_seed:
        if not r["success"]:
            fails[r["reason"]] = fails.get(r["reason"], 0) + 1
    summary = {"seeds": [seed0, count], "success_rate": sum(r["success"] for r in per_seed) / count,
               "first_attempt_success_rate": sum(r["success"] and r["attempts"] == 1 for r in per_seed) / count,
               "failure_breakdown": fails, "per_seed": per_seed}
    print(json.dumps({k: v for k, v in summary.items() if k != "per_seed"}, ensure_ascii=False))
    if out:
        with open(out, "w") as f:
            json.dump(summary, f, ensure_ascii=False, indent=1)
    return summary


def main(root=None, episodes=100, seed=None, allow_retry=False):
    from lerobot.datasets.lerobot_dataset import LeRobotDataset  # S1 수집기 import 시 설치 확인됨
    root = root or DATASET_ROOT
    twin = Rs232UnplugTwin()
    expert = UnplugExpert(twin)
    rng = np.random.default_rng(seed)

    # --- DR 수집 (env-gated, 하위호환): COP_COLLECT_DR=1 이면 조명/마찰/카메라 무작위화 (S1 수집기와 동일 계약) ---
    # 환경치수 불변 — 포트/커넥터/존은 안 건드리고 조명/마찰/카메라 노이즈만 흔들고 매 reset 복원.
    # DR rng 는 배치 rng 와 분리 스트림 → 플러그 배치 시퀀스는 nominal 수집과 동일(비교 가능).
    dr_on = os.environ.get("COP_COLLECT_DR", "") == "1"
    dr_mod = dr_baseline = dr_rng = None
    dr_axes = ()
    dr_noise_std = 0.0
    if dr_on:
        import sim_domain_randomization as dr_mod
        dr_axes = tuple(a.strip() for a in os.environ.get(
            "COP_COLLECT_DR_AXES", "light,friction,camera").split(",") if a.strip())
        dr_baseline = dr_mod.snapshot_baseline(twin.model)
        dr_rng = np.random.default_rng((seed or 0) + 99991)
        print(f"[DR 수집] axes={dr_axes} (환경치수 불변 — 조명/마찰/카메라만 섭동·복원)", flush=True)

    cam_shape = (CAM_H, CAM_W, 3)
    features = {
        "observation.images.top": {"dtype": "video", "shape": cam_shape, "names": ["height", "width", "channels"]},
        "observation.images.closeup": {"dtype": "video", "shape": cam_shape, "names": ["height", "width", "channels"]},
        "observation.state": {"dtype": "float32", "shape": (6,), "names": JOINT_NAMES},
        "action": {"dtype": "float32", "shape": (6,), "names": JOINT_NAMES},
    }
    if os.path.exists(root):
        import shutil
        shutil.rmtree(root)
    dataset = LeRobotDataset.create(repo_id=DATASET_REPO_ID, fps=FPS, features=features, root=root,
                                    robot_type="so101", use_videos=True, vcodec="h264")
    frame_buffer = []

    def record():
        d = twin.data
        top = twin.render("top")
        closeup = twin.render("closeup")
        if dr_on:  # 카메라 센서 노이즈 (top+closeup 둘 다, 측정기와 동일 계약)
            top = dr_mod.apply_camera_noise(top, dr_noise_std, dr_rng)
            closeup = dr_mod.apply_camera_noise(closeup, dr_noise_std, dr_rng)
        frame_buffer.append({
            "task": TASK_LABEL,
            "observation.images.top": top,
            "observation.images.closeup": closeup,
            "observation.state": d.qpos[:6].astype(np.float32).copy(),
            "action": d.ctrl[:6].astype(np.float32).copy(),
        })

    expert.record_hook = record
    saved = attempts = 0
    placements = []
    while saved < episodes and attempts < 2 * episodes:
        attempts += 1
        frame_buffer.clear()
        expert._step_count = 0
        placement = twin.reset(rng)
        if dr_on:  # reset 마다 원본복원 후 무작위화 (누적방지, render 측정기와 동일 순서)
            dr_mod.restore_baseline(twin.model, dr_baseline)
            applied = dr_mod.randomize_scene(twin.model, dr_rng, axes=dr_axes)
            mujoco.mj_setConst(twin.model, twin.data)
            dr_noise_std = applied["camera_noise_std"]
        r = expert.run_episode()
        if r["success"] and frame_buffer and (allow_retry or r["attempts"] == 1) and len(frame_buffer) <= MAX_FRAMES:
            for fr in frame_buffer:
                dataset.add_frame(fr)
            dataset.save_episode()
            placements.append(placement)
            saved += 1
            print(f"[성공 {saved}/{episodes}] 시도#{attempts} frames={len(frame_buffer)} 파지시도={r['attempts']} "
                  f"pcb=({placement['x']:.3f},{placement['y']:.3f},{placement['yaw_deg']:.1f}°)", flush=True)
        else:
            why = (r["reason"] if not r["success"] else f"frames {len(frame_buffer)} > {MAX_FRAMES}" if len(frame_buffer) > MAX_FRAMES
                   else f"재시도 성공(파지시도={r['attempts']}, --allow-retry 없음)")
            print(f"[실패 폐기] 시도#{attempts} 사유={why} pcb=({placement['x']:.3f},{placement['y']:.3f})", flush=True)
    dataset.finalize()
    if placements:
        sidecar = os.path.join(root, "meta", "pcb_traj.json")
        with open(sidecar, "w") as f:
            json.dump({"format": "per-episode PCB placement {x, y, yaw_deg, rejected} (worldbody pcb body)",
                       "save_policy": "success incl. retry" if allow_retry else "first-attempt success only",
                       "episodes": placements}, f)
        print(f"[사이드카] PCB 배치 {len(placements)}ep → {sidecar}")
    print(f"\n수집 완료: {saved}/{episodes} (시도 {attempts}, yield {saved / attempts * 100:.0f}%) → {root}")
    return 0 if saved >= episodes else 1


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="RS232 케이블 분리 closed-loop expert 평가 / 시연 수집 (LeRobot v3, 실기 정렬)")
    p.add_argument("--expert-eval", action="store_true", help="수집 없이 expert 성공률 측정")
    p.add_argument("--seeds", type=int, nargs=2, default=(0, 20), metavar=("START", "COUNT"))
    p.add_argument("--out", default=None, help="expert-eval 요약 JSON 저장 경로")
    p.add_argument("--root", default=None)
    p.add_argument("--episodes", type=int, default=100)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--allow-retry", action="store_true", help="재시도(2차 파지)로 성공한 에피소드도 저장 (기본: 1차 시도 성공만)")
    a = p.parse_args()
    if a.expert_eval:
        expert_eval(*a.seeds, out=a.out)
        raise SystemExit(0)
    raise SystemExit(main(root=a.root, episodes=a.episodes, seed=a.seed, allow_retry=a.allow_retry))
