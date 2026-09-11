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
  - 수집 저장 정책: 기본은 1차 시도 성공 에피소드만 저장(--allow-retry 로 재시도 성공 포함). 1차 실패 구간에는 jaw 가
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


class UnplugExpert(PressExpert):
    """closed-loop 후드 파지-당김. PressExpert 의 ik_point·_phys_step(record 훅) 재사용."""

    def __init__(self, twin: Rs232UnplugTwin):
        super().__init__(twin)
        m = twin.model
        self.HOOD = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "rs232_plug_hood")
        self.JAW_BID = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
        self.ARM_BODIES = {b for b in range(m.nbody) if m.body_rootid[b] == m.body_rootid[self.GBID]}
        self.J_LIFT = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, "shoulder_lift")
        coll = lambda b: [g for g in range(m.ngeom) if m.geom_bodyid[g] == b and (m.geom_contype[g] or m.geom_conaffinity[g])]
        self.G_STATIC, self.G_MOV = coll(self.GBID), coll(self.JAW_BID)
        self._th = 0.0   # 현재 계획의 그리퍼 기울기 [rad]

    # --- 관측 / 운동학 ---
    def _hood(self):
        d = self.t.data
        axis = d.xmat[self.t.plug_bid].reshape(3, 3) @ np.array([-1.0, 0, 0])   # 빠지는 방향(팔 쪽)
        return d.geom_xpos[self.HOOD].copy(), axis, d.xmat[self.t._pcb_bid].reshape(3, 3)[:, 1].copy()

    def _fk(self, q, qg):
        d, di = self.t.data, self.d_ik
        di.qpos[:] = d.qpos
        di.qpos[self.QAD] = q
        di.qpos[5] = qg
        mujoco.mj_forward(self.t.model, di)
        R = di.xmat[self.GBID].reshape(3, 3).copy()
        return R, di.xpos[self.GBID] + R @ GRASP_LOCAL

    def _arm_pen(self, dd):
        """dd 자세에서 팔 geom 의 최소 접촉 dist [m] (플러그 접촉 제외 — 후드 파지 접촉은 의도된 것)과 그 쌍."""
        m = self.t.model
        worst, pair = 0.0, None
        for c in dd.contact[:dd.ncon]:
            b1, b2 = m.geom_bodyid[c.geom1], m.geom_bodyid[c.geom2]
            if self.t.plug_bid in (b1, b2) or not ({b1, b2} & self.ARM_BODIES):
                continue
            if c.dist < worst:
                bn = lambda b: mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, b)
                worst, pair = float(c.dist), (bn(b1), bn(b2))
        return worst, pair

    def _ik(self, target, seed, th):
        """GRASP_LOCAL 을 target 에. th=0 이면 S1 ik_point(그리퍼 z = 월드 수직) 그대로, th>0 이면 그리퍼 z 를 팔 평면
        (shoulder_lift 축에 수직인 연직면) 안에서 바깥쪽으로 th 기울인 방향에 맞춘다 (같은 DLS, 5 관절)."""
        if th == 0.0:
            return self.ik_point(GRASP_LOCAL, target, seed)
        m, di = self.t.model, self.d_ik
        q = np.array(seed, float)
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
            q = q + np.clip(dq, -0.2, 0.2)
        return q

    def _hood_gap(self, geoms):
        m = self.t.model
        return min(mujoco.mj_geomDistance(m, self.d_ik, g, self.HOOD, 0.05, None) for g in geoms)

    def plan_grasp(self, c, axis, y_pcb):
        """무관통·핀치 가능 파지 자세 탐색. 후보 = 기울기(TILTS_DEG, 이전 기울기 해에서 continuation) × 축방향 파지점
        이동(GRASP_SHIFTS) × wrist roll 두 해(±π, 가동 jaw 가 -y_pcb 쪽인 해 우선). 각 후보: IK → jaw 개폐축(gripper x)을
        보드 y 로 roll 정렬 → IK 재계산 후 검사
          (1) IK 오차 < 2mm, jaw 축 어긋남 ≤ ALIGN_MAX_DEG
          (2) 열림(G_OPEN)→접촉각 sweep + 완전 닫힘(G_CLOSE) 팔↔환경 관통 없음 (플러그 접촉 제외)
          (3) 기하 핀치: 접촉각에서 고정 jaw·가동 jaw 모두 후드와 거리 ≤ PINCH_GEOM_TOL
          (4) 당김 경로(닫힘, 1mm 간격, 매 점 IK) 무관통 최대 거리 max_clear ≥ PULL_REQ
        (1)~(3) = grasp_ok, (4) 까지 = feasible. 첫 feasible 후보 반환. 없으면 grasp_ok 중 max_clear 최대 후보
        (fail = margin_blocked if max_clear ≥ FULL else unreachable), grasp_ok 도 없으면 관통 최소 후보(fail=unreachable).
        반환 dict(q, R, target, shift, tilt, align_deg, ik_err, pen, pair, pinch_gap, max_clear, feasible, fail, jaw_side)."""
        best_ok = best_any = None
        cont = {}
        for th_deg in TILTS_DEG:
            th = np.radians(th_deg)
            for shift in GRASP_SHIFTS:
                tgt = c - axis * shift
                out = []
                for flip in (0.0, np.pi):
                    if (shift, flip) in cont:            # 이전 기울기 해에서 continuation (roll 해 유지)
                        q, fl = self._ik(tgt, cont[(shift, flip)], th), 0.0
                    else:
                        q0 = np.array([self.t.data.qpos[a] for a in self.QAD])
                        q0[0] = np.arctan2(tgt[1], tgt[0])
                        q, fl = self.ik_point(GRASP_LOCAL, tgt, q0), flip
                    for k in range(3):
                        R = self._fk(q, G_OPEN)[0]
                        dr = np.arctan2(np.cross(R[:, 0], y_pcb) @ R[:, 2], R[:, 0] @ y_pcb)
                        q[4] += (dr + np.pi / 2) % np.pi - np.pi / 2 + (fl if k == 0 else 0.0)
                        q[4] = (q[4] + np.pi) % (2 * np.pi) - np.pi
                        q = self._ik(tgt, q, th)
                    cont[(shift, flip)] = q.copy()
                    R, p = self._fk(q, G_OPEN)
                    err = float(np.linalg.norm(p - tgt))
                    align = float(np.degrees(np.arccos(min(1.0, abs(R[:, 0] @ y_pcb)))))
                    pen, pair = 0.0, None
                    for g in list(np.linspace(G_OPEN, G_CONTACT, 6)) + [G_CLOSE]:
                        self._fk(q, g)
                        w, pr = self._arm_pen(self.d_ik)
                        if w < pen:
                            pen, pair = w, pr
                    self._fk(q, G_CONTACT)
                    gap = max(self._hood_gap(self.G_STATIC), self._hood_gap(self.G_MOV))
                    grasp_ok = err < 2e-3 and align <= ALIGN_MAX_DEG and pen >= -KIN_PEN_TOL and gap <= PINCH_GEOM_TOL
                    clear = 0.0
                    if grasp_ok:   # 당김 경로: 1mm 간격, 첫 관통 지점 직전까지가 무관통 최대 거리
                        qp = q
                        for dist in list(np.arange(0.001, PULL_REQ, 0.001)) + [PULL_REQ]:
                            qp = self._ik(tgt + axis * dist, qp, th)
                            self._fk(qp, G_CONTACT)
                            w, pr = self._arm_pen(self.d_ik)
                            if w < -KIN_PEN_TOL:
                                pair = pr
                                break
                            clear = float(dist)
                    cand = dict(q=q, R=R, target=tgt, shift=shift, tilt=th, align_deg=align, ik_err=err, pen=pen, pair=pair,
                                pinch_gap=gap, max_clear=clear, grasp_ok=grasp_ok, feasible=grasp_ok and clear >= PULL_REQ - 1e-9,
                                jaw_side=float(R[:, 0] @ y_pcb))
                    out.append(cand)
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

    def step_to(self, q_arm, n, g=None):
        d = self.t.data
        cur, g0 = d.ctrl[:5].copy(), float(d.ctrl[5])
        g = g0 if g is None else g
        for s in range(n):
            tt = (s + 1) / n
            d.ctrl[:5] = cur + (q_arm - cur) * tt
            d.ctrl[5] = g0 + (g - g0) * tt
            self._phys_step()

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
        """step_to + 단계 끝 팔 관통 기록 (플러그 접촉 제외)."""
        self.step_to(q_arm, n, g)
        w, pair = self._arm_pen(self.t.data)
        if w < self._ep_pen[0]:
            self._ep_pen = (w, pair)

    def run_episode(self):
        """홈에서 분리 1회. 성공 = 핀치 확인 + FULL latch + 변위 ≥ 1.5×FULL.
        반환 dict(success, attempts, reason(마지막 시도 사유), history(시도별 진단)).
        사유: unreachable(파지 자세 불가 또는 FULL 이전 당김 경로 관통, 미실행) / margin_blocked(FULL 까지 무관통,
              PULL_REQ 이전 관통, 미실행) / approach_blocked / grasp_miss / grasp_slip / jam /
              short_pull / threshold_not_reached.
        파지 확인(고정·가동 jaw 모두 후드 접촉) 없이는 당기지 않는다 — 한쪽 jaw 로 누르고 끄는 비핀치 분리는
        실기 재현 위험이 커서 시연으로 쓰지 않는다."""
        t, d = self.t, self.t.data
        self._ep_pen = (0.0, None)   # 시도별 팔 관통 최소값 (플러그 제외) — 매 시도 시작 시 리셋
        c, axis, y_pcb = self._hood()
        plan = self.plan_grasp(c, axis, y_pcb)
        history = []
        qpan = np.array(d.ctrl[:5]); qpan[0] = plan["q"][0]
        self._stage(qpan, 200)
        reason = None
        for attempt in range(MAX_ATTEMPTS_PER_EP):
            if attempt:                              # 재관측 (closed-loop) 후 재계획
                c, axis, y_pcb = self._hood()
                plan = self.plan_grasp(c, axis, y_pcb)
            tgt, self._th = plan["target"], plan["tilt"]
            att = {"attempt": attempt + 1, "plan_feasible": plan["feasible"], "plan_ik_err_mm": round(plan["ik_err"] * 1e3, 2),
                   "plan_pen_mm": round(plan["pen"] * 1e3, 2), "plan_pen_pair": plan["pair"],
                   "grasp_shift_mm": round(plan["shift"] * 1e3, 1), "tilt_deg": round(float(np.degrees(plan["tilt"])), 1),
                   "align_deg": round(plan["align_deg"], 1), "pinch_gap_mm": round(plan["pinch_gap"] * 1e3, 2),
                   "max_clear_pull_mm": round(plan["max_clear"] * 1e3, 1),
                   "moving_jaw_side": "-y" if plan["jaw_side"] < 0 else "+y"}
            history.append(att)
            self._ep_pen = (0.0, None)
            if not plan["feasible"]:
                # 이 파지 계열(기울기·이동·roll)로 무관통·핀치 가능한 파지+당김 자세가 없음. 실행하면 팔이 자기 링크에 막힌 채
                # 우연히 잡는 비정상 시연이 나온다(2026-09-11 측정: seed 2·12 가 shoulder↔jaw 접촉 -0.5/-1.4mm, 접근 오차 6/13mm).
                att["reason"] = reason = plan["fail"]
                break
            side = -SIDE_CLEAR * plan["R"][:, 0]    # 고정 jaw(gripper -x 쪽)를 후드 측면에서 띄움
            qc = self._ik(tgt + side + [0, 0, WAYPOINT_Z], plan["q"], self._th)
            self._stage(qc, 300)
            self._stage(qc, 120, g=G_OPEN)
            for dz in DESCENT_Z:
                qc = self._ik(tgt + side + [0, 0, dz], self._q(), self._th)
                self._stage(qc, 150)
            qc = self._ik(tgt, self._q(), self._th)
            self._stage(qc, 100)
            approach_err = float(np.linalg.norm(self._tcp() - tgt))
            self._stage(qc, 250, g=G_CLOSE)
            self._stage(qc, 100)
            pinch = all(self._hood_contacts())
            att.update(attempt=attempt + 1, approach_err_mm=round(approach_err * 1e3, 2), pinch=pinch)

            if pinch:   # 당김: 커넥터 축으로 2mm 씩, 매 단계 IK 재계산, 핀치 풀리면 중단
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
            self._stage(np.array(self._q()), 150, g=G_OPEN)
            up = self._ik(self._tcp() + [0, 0, WAYPOINT_Z], self._q(), self._th)
            self._stage(up, 250)
            att.update(final_disp_mm=round(t.plug_displacement() * 1e3, 2),
                        episode_arm_pen_mm=round(self._ep_pen[0] * 1e3, 2), episode_arm_pen_pair=self._ep_pen[1])
            if pinch and t.unplugged_full() and t.plug_displacement() >= PULL_DISP:
                att["reason"] = "ok"
                return {"success": True, "attempts": attempt + 1, "reason": "ok", "history": history}

            if approach_err > 3e-3:
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
        frame_buffer.append({
            "task": TASK_LABEL,
            "observation.images.top": twin.render("top"),
            "observation.images.closeup": twin.render("closeup"),
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
        r = expert.run_episode()
        if r["success"] and frame_buffer and (allow_retry or r["attempts"] == 1):
            for fr in frame_buffer:
                dataset.add_frame(fr)
            dataset.save_episode()
            placements.append(placement)
            saved += 1
            print(f"[성공 {saved}/{episodes}] 시도#{attempts} frames={len(frame_buffer)} 파지시도={r['attempts']} "
                  f"pcb=({placement['x']:.3f},{placement['y']:.3f},{placement['yaw_deg']:.1f}°)", flush=True)
        else:
            why = r["reason"] if not r["success"] else f"재시도 성공(파지시도={r['attempts']}, --allow-retry 없음)"
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
