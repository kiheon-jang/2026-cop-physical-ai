"""Phase 4 W1 — 3단계 RS232(HHT) 케이블 분리 트윈.

sim_pcb_reset.py(S1)와 같은 형태·같은 규약:
  1. 분리 판정 = 사람 눈이 아니라 **플러그 슬라이드 조인트 변위 임계** latch
     (수집기·평가기가 이 모듈의 UNPLUG_* 상수를 import 해서 공유)
  2. PCB 배치 무작위화 = S1 존 상수 그대로 import (환경 불변 원칙)
  3. top / closeup 640×480 렌더 — 실기 관측 스키마와 동일 이름

커넥터 / 판정 근거 (DE-9, E 쉘):
  - 접점 분리력: Cinch M24308(MIL-C-24308) 데이터시트 "Individual Contact Insertion and
    Separation Force (min/max): 0.7 oz / 12 oz" = 0.195 N / 3.34 N per contact.
    9핀 대역 = 1.75 N(최소 분리력) ~ 30 N(최대 삽입력).
    보유력 = 9 × 0.8 N(대역의 로그 중앙 √(0.195×3.34)=0.81 N) ≈ 7.2 N
    → 씬 XML 슬라이드 frictionloss="7.2" (쿨롱 마찰, 단일 출처 = XML).
    나사(잭스크류) 미체결 가정 — 실기 HHT 플러그 실측(당김 저울) 수신 시 교정할 노브.
  - UNPLUG_FULL_M = 5.90 mm: D 쉘 돌출(Adam Tech DXXX-SR 도면 DE09, .232"=5.90mm) = 최대 결합 깊이.
    핀은 쉘 안에 있으므로 핀 결합 길이 ≤ 쉘 깊이 → 핀 길이와 무관하게 핀·쉘 모두 이탈
    (기계적으로 빠짐). 핀 결합 길이 자체는 1차 출처 미확보라 더 엄격한 쉘 깊이를 택함.
  - UNPLUG_PARTIAL_M = FULL/2 = 2.95 mm: 결합 깊이의 절반 이상 빠짐(헐거워졌으나 미분리).
    규격 근거가 아닌 정의값 — 부분성공 지표 전용, 성공 판정은 FULL.

배치 거부 샘플링: S1 존 근단(PCB x≈0.15)에선 팔 쪽으로 ~37mm 돌출한 플러그/포트가 홈 자세 팔
shoulder 메쉬와 겹친다(물리적으로 불가능한 배치). reset 은 존 상수는 그대로 두고 초기 관통 배치만
다시 뽑는다. S1 씬도 같은 존에서 보드↔팔 관통 배치가 나온다(rng0 200회 중 10회 5.0%, 최대 8.8mm,
2026-09-11 측정) — S1 은 수정 금지라 기록만.

headless 전용 (mujoco.Renderer).
"""
import os
import numpy as np
import mujoco as mj

from sim_pcb_reset import CAM_W, CAM_H, FPS, CAMERA_NAMES, ZONE_X, ZONE_Y, ZONE_YAW_DEG

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCENE_PATH = os.path.join(BASE, "sim/assets/rs232_unplug_scene.xml")

# A7 RS232 전용 HOME: S1 HOME_QPOS 의 shoulder_lift -1.6(-91.67°)은 실기 펌웨어 위치한계(-89.54°) 밖이라 명령 불가 →
# 하한으로 클립, 나머지 유지 (SPEC §1.2). S1 HOME 은 불변. 이 모듈의 HOME_QPOS 를 쓰는 reset·수집기·측정기 공통.
HOME_QPOS = (0.0, -1.56274, 1.4, 0.9, 0.0, 0.0)

TASK_LABEL = "unplug the rs232 cable"

# 판정 임계 (슬라이드 변위, 빠지는 방향 +)
UNPLUG_FULL_M = 0.0059       # D 쉘 결합 깊이 5.90mm → 핀·쉘 완전 이탈
UNPLUG_PARTIAL_M = UNPLUG_FULL_M / 2

PENETRATION_TOL_M = 1e-4     # 초기 관통 허용 한계
MAX_RESAMPLE = 100

# DE-9 접점 분리력 대역 (Cinch M24308 per-contact 0.7oz/12oz × 9핀) — self-check 가 보유력 검증에 사용
DE9_CONTACTS = 9
CONTACT_FORCE_BAND_N = (0.195, 3.34)


class Rs232UnplugTwin:
    def __init__(self, scene_path: str = SCENE_PATH):
        self.model = mj.MjModel.from_xml_path(scene_path)
        self.data = mj.MjData(self.model)
        self._pcb_bid = mj.mj_name2id(self.model, mj.mjtObj.mjOBJ_BODY, "pcb")
        self.plug_bid = mj.mj_name2id(self.model, mj.mjtObj.mjOBJ_BODY, "rs232_plug")
        jid = mj.mj_name2id(self.model, mj.mjtObj.mjOBJ_JOINT, "rs232_plug_slide")
        self._plug_qadr = self.model.jnt_qposadr[jid]
        self.plug_dof = self.model.jnt_dofadr[jid]
        self._full_latch = False
        self._partial_latch = False
        self._renderer = None

    # ── 에피소드 리셋 + 존 무작위화 (S1 PcbResetTwin.reset 과 동일 분포) ─────
    def reset(self, rng: np.random.Generator | None = None) -> dict:
        """mj_resetData + (rng 주면) PCB 를 S1 존 안에 재배치, 초기 관통 배치는 재추첨.
        반환 dict 의 rejected = 이번 reset 에서 버린 관통 배치 수."""
        mj.mj_resetData(self.model, self.data)
        self._full_latch = self._partial_latch = False
        self.data.qpos[:6] = HOME_QPOS
        self.data.ctrl[:6] = HOME_QPOS
        placement = {"x": None, "y": None, "yaw_deg": 0.0, "rejected": 0}
        for rejected in range(MAX_RESAMPLE if rng is not None else 1):
            if rng is not None:
                x = float(rng.uniform(*ZONE_X))
                y = float(rng.uniform(*ZONE_Y))
                yaw = float(rng.uniform(-ZONE_YAW_DEG, ZONE_YAW_DEG))
                self.model.body_pos[self._pcb_bid][:2] = (x, y)
                half = np.deg2rad(yaw) / 2.0
                self.model.body_quat[self._pcb_bid] = (np.cos(half), 0, 0, np.sin(half))
                placement = {"x": x, "y": y, "yaw_deg": yaw, "rejected": rejected}
            mj.mj_forward(self.model, self.data)
            if self.min_contact_dist() >= -PENETRATION_TOL_M:
                return placement
        raise RuntimeError(f"관통 없는 배치를 {MAX_RESAMPLE}회 안에 못 찾음: {placement}")

    def min_contact_dist(self) -> float:
        return min((float(c.dist) for c in self.data.contact[:self.data.ncon]), default=0.0)

    # ── 판정 ──────────────────────────────────────────────────────────────
    def plug_displacement(self) -> float:
        """플러그가 결합 위치에서 빠진 거리 [m] (팔 방향 +)."""
        return float(self.data.qpos[self._plug_qadr])

    def unplugged_full(self) -> bool:
        return self._full_latch

    def unplugged_partial(self) -> bool:
        return self._partial_latch

    def step(self):
        mj.mj_step(self.model, self.data)
        disp = self.plug_displacement()
        self._partial_latch |= disp >= UNPLUG_PARTIAL_M
        self._full_latch |= disp >= UNPLUG_FULL_M

    # ── 렌더 ──────────────────────────────────────────────────────────────
    def render(self, camera: str) -> np.ndarray:
        assert camera in CAMERA_NAMES, f"unknown camera '{camera}' (실기 정렬: {CAMERA_NAMES})"
        if self._renderer is None:
            self._renderer = mj.Renderer(self.model, height=CAM_H, width=CAM_W)
        self._renderer.update_scene(self.data, camera=camera)
        return self._renderer.render()

    def close(self):
        if self._renderer is not None:
            self._renderer.close()
            self._renderer = None


def _in_top_view(m, d, gid):
    """geom 박스 8 꼭짓점이 top 카메라(핀홀) 이미지 안에 모두 들어오는가."""
    cid = mj.mj_name2id(m, mj.mjtObj.mjOBJ_CAMERA, "top")
    f = (CAM_H / 2) / np.tan(np.deg2rad(m.cam_fovy[cid]) / 2)
    Rc, pc = d.cam_xmat[cid].reshape(3, 3), d.cam_xpos[cid]
    Rg, pg, s = d.geom_xmat[gid].reshape(3, 3), d.geom_xpos[gid], m.geom_size[gid]
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                p = Rc.T @ (pg + Rg @ (s * (sx, sy, sz)) - pc)
                if p[2] >= 0:
                    return False
                u = CAM_W / 2 + f * p[0] / -p[2]
                v = CAM_H / 2 - f * p[1] / -p[2]
                if not (0 <= u < CAM_W and 0 <= v < CAM_H):
                    return False
    return True


def _pinch_pull(twin, ex, pinch=True):
    """물리 파지-당김 1회 (self-check 용 조잡한 스크립트, expert 아님).
    팔을 파지 직전 자세에 놓고 → jaw 를 보드 y 에 정렬해 후드 양 측면(±y)을 집고 → 커넥터 축(팔 쪽)으로
    2mm 씩 IK 재계산하며 최대 20mm 당김. pinch=False 면 jaw 를 연 채 같은 궤적(무핀치 대조군).
    파지 오프셋(gripperframe 에서 그리퍼 x -20mm, z +4mm, 열림 0.8)은 25 배치 충돌 없는 파지 자세 탐색에서
    25/25 동일하게 나온 값. 반환: (FULL, 최종 변위 m, 첫 4mm 구간 slip/TCP 축이동 비, 최종 TCP 추종오차 m,
    파지 직전 최소 접촉 dist m)."""
    m, d, di, QAD = twin.model, twin.data, ex.d_ik, ex.QAD
    hood = mj.mj_name2id(m, mj.mjtObj.mjOBJ_GEOM, "rs232_plug_hood")
    local = m.site_pos[mj.mj_name2id(m, mj.mjtObj.mjOBJ_SITE, "gripperframe")].copy()
    c = d.geom_xpos[hood].copy()
    y_pcb = d.xmat[twin._pcb_bid].reshape(3, 3)[:, 1]
    axis = d.xmat[twin.plug_bid].reshape(3, 3) @ np.array([-1.0, 0, 0])

    def grip_R(q):
        di.qpos[:] = d.qpos
        di.qpos[QAD] = q
        mj.mj_forward(m, di)
        return di.xmat[ex.GBID].reshape(3, 3).copy()

    q = np.array(HOME_QPOS[:5], float)
    q[0] = np.arctan2(c[1], c[0])
    q = ex.ik_point(local, c, q)
    xh = grip_R(q)[:2, 0]
    q[4] += (np.arctan2(y_pcb[1], y_pcb[0]) - np.arctan2(xh[1], xh[0]) + np.pi / 2) % np.pi - np.pi / 2
    q = ex.ik_point(local, c, q)
    tgt = c - 0.020 * grip_R(q)[:, 0] + np.array([0, 0, 0.004])
    q = ex.ik_point(local, tgt, q)
    g_open, g_close = 0.8, (0.25 - 0.4 if pinch else 0.8)   # jaw 가 후드에 닿는 각 0.25 에서 0.4rad 더 조임

    d.qpos[QAD], d.qpos[5] = q, g_open
    d.ctrl[:5], d.ctrl[5] = q, g_open
    mj.mj_forward(m, d)
    pre_dist = twin.min_contact_dist()
    for _ in range(100):
        twin.step()
    for k in range(250):
        d.ctrl[5] = g_open + (g_close - g_open) * (k + 1) / 250
        twin.step()
    for _ in range(100):
        twin.step()

    tcp = lambda: d.xpos[ex.GBID] + d.xmat[ex.GBID].reshape(3, 3) @ local
    rel = lambda: (tcp() - d.xpos[twin.plug_bid]) @ axis   # 플러그 기준 그리퍼 축방향 위치 — 변하면 slip
    r0, p0, slip_ratio = rel(), tcp(), None
    qc = d.qpos[QAD].copy()
    for dmm in range(2, 21, 2):
        goal = tgt + axis * dmm * 1e-3
        qc = ex.ik_point(local, goal, qc)
        cur = d.ctrl[:5].copy()
        for k in range(150):
            d.ctrl[:5] = cur + (qc - cur) * (k + 1) / 150
            twin.step()
        if dmm == 4:
            trav = (tcp() - p0) @ axis
            slip_ratio = (rel() - r0) / trav if trav > 1e-3 else None
        if twin.unplugged_full():
            break
    return twin.unplugged_full(), twin.plug_displacement(), slip_ratio, float(np.linalg.norm(goal - tcp())), pre_dist


def _self_check():  # noqa: C901
    twin = Rs232UnplugTwin()
    m, d = twin.model, twin.data
    name = lambda ty, i: mj.mj_id2name(m, ty, i)
    hood = mj.mj_name2id(m, mj.mjtObj.mjOBJ_GEOM, "rs232_plug_hood")
    plug_bodies = {twin.plug_bid}
    plugport = plug_bodies | {mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, "rs232_port")}
    F_ret = float(m.dof_frictionloss[twin.plug_dof])

    # 1. 로드 + 그리퍼↔플러그 접촉 필터가 살아 있는가
    assert m.nu == 6, f"actuator 6 기대, {m.nu}"
    for cam in CAMERA_NAMES:
        assert mj.mj_name2id(m, mj.mjtObj.mjOBJ_CAMERA, cam) >= 0, f"camera '{cam}' 없음"
    excl = {(int(s) >> 16, int(s) & 0xFFFF) for s in m.exclude_signature}
    jaw_geoms = [g for g in range(m.ngeom)
                 if name(mj.mjtObj.mjOBJ_BODY, m.geom_bodyid[g]) in ("gripper", "moving_jaw_so101_v1")
                 and (m.geom_contype[g] or m.geom_conaffinity[g])]
    assert len(jaw_geoms) >= 2, "그리퍼 충돌 geom 없음"
    for g in jaw_geoms:
        b1, b2 = sorted((int(m.geom_bodyid[g]), twin.plug_bid))
        assert (m.geom_contype[g] & m.geom_conaffinity[hood]) or (m.geom_contype[hood] & m.geom_conaffinity[g])
        assert (b1, b2) not in excl, "그리퍼↔플러그 접촉이 exclude 됨"
    print(f"[1] 로드 OK — 그리퍼 충돌 geom {len(jaw_geoms)}개 ↔ 후드 접촉 필터 활성, 보유력 frictionloss={F_ret} N")

    # 2. 결정론 + 존 경계
    assert twin.reset(np.random.default_rng(42)) == twin.reset(np.random.default_rng(42)), "seed 42 재현 실패"
    print("[2] seed 42 배치 재현 OK")

    # 3. 무작위 리셋 200회(≥20): 존 경계 + 초기 관통 없음 + 후드 top 시야 안 + latch 해제, 거부율 측정
    N = 200
    rng = np.random.default_rng(0)
    worst, rejected = 0.0, 0
    # 실제 가시성: 세그멘테이션 렌더의 후드 픽셀 수. 홈 자세(S1 HOME_QPOS)의 접힌 팔이 팔 쪽 가장자리를
    # top 에서 가릴 수 있어 프러스텀만으론 부족 — 매 리셋 "두 카메라 중 하나 이상에 보임"을 요구하고
    # top 가림은 수치로 보고한다. 팔 제외 기준 = 팔 visual mesh(group 2) 숨김.
    seg = mj.Renderer(m, height=CAM_H, width=CAM_W)
    seg.enable_segmentation_rendering()
    no_arm = mj.MjvOption()
    no_arm.geomgroup[2] = 0

    def hood_px(cam, opt=None):
        seg.update_scene(d, camera=cam, scene_option=opt)
        s = seg.render()
        return int(((s[..., 0] == hood) & (s[..., 1] == mj.mjtObj.mjOBJ_GEOM)).sum())
    top_frac, top_hidden, cl_min = [], 0, None
    for i in range(N):
        p = twin.reset(rng)
        rejected += p["rejected"]
        assert ZONE_X[0] <= p["x"] <= ZONE_X[1] and ZONE_Y[0] <= p["y"] <= ZONE_Y[1], p
        assert abs(p["yaw_deg"]) <= ZONE_YAW_DEG
        assert not twin.unplugged_partial() and not twin.unplugged_full()
        assert twin.plug_displacement() == 0.0
        worst = min(worst, twin.min_contact_dist())
        assert worst >= -PENETRATION_TOL_M, f"초기 관통 {worst*1000:.2f}mm"
        assert _in_top_view(m, d, hood), f"리셋 {i}: 후드가 top 시야 밖 {p}"
        top_full, top_vis, cl_vis = hood_px("top", no_arm), hood_px("top"), hood_px("closeup")
        assert top_full > 0, f"리셋 {i}: 팔 없이도 top 에 후드 픽셀 0"
        assert top_vis > 0 or cl_vis > 0, f"리셋 {i}: 두 카메라 모두 후드 안 보임 {p}"
        top_frac.append(top_vis / top_full)
        top_hidden += top_vis == 0
        cl_min = cl_vis if cl_min is None else min(cl_min, cl_vis)
    seg.close()
    top_frac = np.array(top_frac)
    print(f"[3] 무작위 리셋 {N}회 — 관통 없음(최소 dist {worst*1000:.3f}mm), 관통 배치 거부 {rejected}회 "
          f"(거부율 {rejected/(N+rejected):.1%}), 후드 top 프러스텀 {N}/{N}, 두 카메라 중 하나 이상 가시 {N}/{N} "
          f"(closeup 최소 {cl_min}px); top 팔 가림: 완전 가림 {top_hidden}/{N}, 가시<50% {(top_frac < 0.5).sum()}/{N}, "
          f"평균 가시 {top_frac.mean():.0%}")

    # 4. 무접촉 3초 중력만 → 변위 < 0.5mm (슬라이드 축은 수평이라 중력 축성분 0 — 솔버 드리프트 검사)
    twin.reset(np.random.default_rng(7))
    for _ in range(int(3.0 / m.opt.timestep)):
        twin.step()
        for c in d.contact[:d.ncon]:
            assert not ({int(m.geom_bodyid[c.geom1]), int(m.geom_bodyid[c.geom2])} & plugport), "플러그 접촉 발생"
    g_disp = twin.plug_displacement()
    assert abs(g_disp) < 5e-4 and not twin.unplugged_partial(), f"중력만으로 {g_disp*1000:.3f}mm"
    print(f"[4] 중력만 3초 — 변위 {g_disp*1000:.4f}mm (< 0.5mm)")

    def pull(force_fn, seconds):
        """플러그 body 에 커넥터 축(팔 방향) 외력. 반환: (최종 변위, 첫 partial 시각, 첫 full 시각)."""
        axis = d.xmat[twin.plug_bid].reshape(3, 3) @ np.array([-1.0, 0, 0])
        t_part = t_full = None
        n = int(seconds / m.opt.timestep)
        for k in range(n):
            t = k * m.opt.timestep
            d.xfrc_applied[twin.plug_bid, :3] = force_fn(t) * axis
            twin.step()
            if t_part is None and twin.unplugged_partial():
                t_part = t
            if t_full is None and twin.unplugged_full():
                t_full = t
        d.xfrc_applied[twin.plug_bid, :3] = 0
        return twin.plug_displacement(), t_part, t_full

    # 5a. 보유력 이하(0.8×) 2초 유지 → 빠지지 않음
    twin.reset(np.random.default_rng(7))
    disp_hold, _, _ = pull(lambda t: 0.8 * F_ret, 2.0)
    assert disp_hold < 5e-4, f"0.8×보유력에서 {disp_hold*1000:.3f}mm 빠짐"
    # 5b. 램프 0→2× 보유력(4초): 이탈 시작 힘(변위 0.5mm) 측정
    twin.reset(np.random.default_rng(7))
    ramp = lambda t: 2.0 * F_ret * t / 4.0
    axis = d.xmat[twin.plug_bid].reshape(3, 3) @ np.array([-1.0, 0, 0])
    F_break = None
    for k in range(int(4.0 / m.opt.timestep)):
        d.xfrc_applied[twin.plug_bid, :3] = ramp(k * m.opt.timestep) * axis
        twin.step()
        if twin.plug_displacement() >= 5e-4:
            F_break = ramp(k * m.opt.timestep)
            break
    d.xfrc_applied[twin.plug_bid, :3] = 0
    assert F_break is not None and 0.9 * F_ret <= F_break <= 1.2 * F_ret, f"이탈 힘 {F_break} (보유력 {F_ret})"
    lo, hi = (DE9_CONTACTS * f for f in CONTACT_FORCE_BAND_N)
    assert lo <= F_break <= hi, f"이탈 힘 {F_break:.2f}N 이 DE-9 규격 대역 [{lo:.2f},{hi:.1f}] 밖"
    # 5c. 1.5× 보유력 일정 → partial → full 순서로 latch, 되밀어도 latch 유지
    twin.reset(np.random.default_rng(7))
    disp_pull, t_part, t_full = pull(lambda t: 1.5 * F_ret, 1.0)
    assert twin.unplugged_full() and t_part is not None and t_full is not None and t_part <= t_full, \
        f"1.5×보유력 1초에 FULL 미도달 (변위 {disp_pull*1000:.2f}mm)"
    d.qpos[twin._plug_qadr] = 0.0
    twin.step()
    assert twin.unplugged_full() and twin.unplugged_partial(), "되꽂음에 latch 가 풀림"
    # 5d. 0.95× 보유력 3초 → PARTIAL 도 미도달 (보유력 바로 아래 축하중 대조군)
    twin.reset(np.random.default_rng(7))
    disp_95, _, _ = pull(lambda t: 0.95 * F_ret, 3.0)
    assert not twin.unplugged_partial(), f"0.95×보유력 3초에 PARTIAL ({disp_95*1000:.3f}mm)"
    print(f"[5] 외력 당김 — 0.8×({0.8*F_ret:.2f}N) 2초 변위 {disp_hold*1000:.4f}mm / "
          f"이탈 시작 {F_break:.2f}N (규격 대역 {lo:.2f}~{hi:.1f}N) / "
          f"1.5×({1.5*F_ret:.1f}N): PARTIAL {t_part*1000:.0f}ms, FULL {t_full*1000:.0f}ms, 1초 후 {disp_pull*1000:.1f}mm, latch 유지 / "
          f"0.95×({0.95*F_ret:.2f}N) 3초 {disp_95*1000:.3f}mm latch 없음")

    # 6. 물리 파지-당김 — 그리퍼↔후드 마찰이 크리프 없이 보유력을 전달하는가 (회귀 = 파지 slip).
    #    25 존 배치(rng 2026)에 같은 파지 레시피. 파지 직전 자세가 관통(팔 자기충돌 포함)하는 배치는 실물로 불가능한
    #    자세라 제외하고 수를 보고 — 존 근단(x≲0.215)에서 열린 moving_jaw 가 shoulder 링크와 최대 7.8mm 겹침(4/25, 2026-09-11).
    #    유효 배치 ≥ 15 에서: 핀치-당김 전부 FULL, 첫 4mm 당김 slip/TCP이동 비 < 0.2.
    #    대조군: 같은 배치·같은 궤적, jaw 열림 → FULL 0, 변위 < 0.5mm.
    #    씬 접촉을 MuJoCo 기본(pyramidal·impratio 1·후드 solref 0.02)으로 되돌리거나 둘 중 하나만 쓰면 이 검사가 실패 (2026-09-11 측정).
    from sim_pcb_reset_collector import PressExpert   # S1 IK 재사용 (lerobot import 가 무거워 지연 import)
    ex = PressExpert(twin)
    K = 25
    runs = {}
    for pinch in (True, False):
        rng = np.random.default_rng(2026)
        runs[pinch] = [(twin.reset(rng), _pinch_pull(twin, ex, pinch)) for _ in range(K)]
    valid = [i for i in range(K) if runs[True][i][1][4] >= -5e-4]
    skipped = [(round(runs[True][i][0]["x"], 3), round(runs[True][i][1][4] * 1000, 1)) for i in range(K) if i not in valid]
    assert len(valid) >= 15, f"충돌 없는 파지 직전 자세 {len(valid)}/{K} (제외 x,dist mm: {skipped})"
    pin = [(runs[True][i][0], runs[True][i][1]) for i in valid]
    opn = [runs[False][i][1] for i in valid]
    fails = [(round(p["x"], 3), round(r[1] * 1000, 2)) for p, r in pin if not r[0]]
    ratios = [r[2] for _, r in pin if r[2] is not None]
    assert not fails, f"핀치-당김 비FULL {len(fails)}/{len(valid)} (x, 변위mm): {fails}"
    assert max(ratios) < 0.2, f"파지 slip — slip/TCP이동 비 최대 {max(ratios):.2f}"
    open_disp = max(abs(r[1]) for r in opn)
    assert not any(r[0] for r in opn) and open_disp < 5e-4, f"jaw 열림 대조군이 플러그를 움직임 {open_disp*1000:.2f}mm"
    print(f"[6] 물리 파지-당김 — 충돌 없는 파지 직전 자세 {len(valid)}/{K} (제외 x,dist mm {skipped}), "
          f"핀치 FULL {len(valid)}/{len(valid)}, slip/TCP이동 비 중앙 {np.median(ratios):+.2f} 최대 {max(ratios):+.2f} (n={len(ratios)}); "
          f"jaw 열림 대조군 FULL 0/{len(valid)}, 최대 변위 {open_disp*1000:.3f}mm")

    # 7. 렌더: 두 카메라 640×480, 내용 있는 프레임
    twin.reset(np.random.default_rng(42))
    for cam in CAMERA_NAMES:
        img = twin.render(cam)
        assert img.shape == (CAM_H, CAM_W, 3), img.shape
        assert float(img.std()) > 5.0, f"{cam} 렌더가 비어 있음 (std={img.std():.2f})"
    print(f"[7] 렌더 {CAMERA_NAMES} {CAM_W}×{CAM_H} OK")

    twin.close()
    print("sim_rs232_unplug self-check: 7/7 PASS "
          f"(PARTIAL {UNPLUG_PARTIAL_M*1000:.2f}mm, FULL {UNPLUG_FULL_M*1000:.1f}mm, 보유력 {F_ret}N)")


# 실기 정합 관절 한계 [rad] (SPEC §1.1): 팔 4축 = follower 캘리브 = 펌웨어 위치한계, wrist_roll·gripper = URDF. self-check [8] 기준값.
REAL_JOINT_RANGE = {
    "shoulder_pan": (-1.74379, 1.74379), "shoulder_lift": (-1.56274, 1.56274), "elbow_flex": (-1.68702, 1.68702),
    "wrist_flex": (-1.63025, 1.63025), "wrist_roll": (-2.74385, 2.84121), "gripper": (-0.17453, 1.74533),
}


def _self_check_real():  # noqa: C901
    """실기 정합 확장 [8][9][11]. [10]·[12](원본 대비) 는 원본 트윈이 필요해 check_vs_orig.py 에 있음."""
    twin = Rs232UnplugTwin()
    m, d = twin.model, twin.data
    B = mj.mjtObj.mjOBJ_BODY
    bn = lambda b: mj.mj_id2name(m, B, int(b))
    home = np.array(HOME_QPOS)

    # 8. 관절 한계 = 스펙 값 (range·ctrlrange), HOME 이 한계 안, 한계 밖 명령 시 한계에서 막힘.
    #    검사용 모델 사본은 접촉을 꺼서(팔↔바닥·base 가 한계 도달을 가로막지 않게) 관절 한계만 본다.
    #    (a) ctrlrange 클램프(=펌웨어 Goal 클램프) 켠 상태 (b) 클램프를 끈 사본 = 관절 range 자체가 정지시키는가.
    for jn, r in REAL_JOINT_RANGE.items():
        jid = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, jn)
        aid = mj.mj_name2id(m, mj.mjtObj.mjOBJ_ACTUATOR, jn)
        assert m.jnt_limited[jid] and np.allclose(m.jnt_range[jid], r, rtol=0, atol=1e-9), (jn, m.jnt_range[jid])
        assert m.actuator_ctrllimited[aid] and np.allclose(m.actuator_ctrlrange[aid], r, rtol=0, atol=1e-9), (jn, m.actuator_ctrlrange[aid])
    lim = m.jnt_range[:6]
    assert np.all(home >= lim[:, 0]) and np.all(home <= lim[:, 1]), f"HOME 이 한계 밖 {home}"
    worst = {}
    for clamp in (True, False):
        m2 = mj.MjModel.from_xml_path(SCENE_PATH)
        m2.opt.disableflags |= mj.mjtDisableBit.mjDSBL_CONTACT
        if not clamp:
            m2.actuator_ctrllimited[:6] = 0
        beyond, gap = 0.0, 0.0
        for j in range(6):
            for side, sgn in ((0, -1.0), (1, 1.0)):
                d2 = mj.MjData(m2)
                d2.qpos[:6] = home
                d2.ctrl[:6] = home
                d2.ctrl[j] = lim[j, side] + sgn * 0.5          # 한계 밖 0.5rad 명령
                for _ in range(int(2.0 / m2.opt.timestep)):
                    mj.mj_step(m2, d2)
                over = sgn * (d2.qpos[j] - lim[j, side])       # + = 한계 넘어감
                beyond, gap = max(beyond, over), max(gap, -over)
        worst[clamp] = (np.degrees(beyond), np.degrees(gap))
    # 측정(2026-09-11): 클램프 켬 최대 0.013°, 클램프 끔(2.94N·m 로 한계를 밈) 소프트 한계 관통 최대 0.12°
    assert worst[True][0] < 0.1 and worst[True][1] < 0.1, f"클램프 켬: 넘어감/미도달 {worst[True]}°"
    assert worst[False][0] < 0.25 and worst[False][1] < 0.25, f"클램프 끔: 관절 range 가 못 막음 {worst[False]}°"
    print(f"[8] 관절 한계 = 스펙 {len(REAL_JOINT_RANGE)}축 (range·ctrlrange), HOME 한계 안; 한계 밖 0.5rad 명령 2초 — "
          f"ctrlrange 클램프: 최대 넘어감 {worst[True][0]:.3f}° 미도달 {worst[True][1]:.3f}° / "
          f"클램프 끔(관절 range 만): 최대 관통 {worst[False][0]:.3f}° 미도달 {worst[False][1]:.3f}°")

    # 9. base 충돌 활성. 검사 전용 MjData 로 운동학(mj_forward)만.
    bc = mj.mj_name2id(m, B, "base_collision")
    sh = mj.mj_name2id(m, B, "shoulder")
    g_bc = [g for g in range(m.ngeom) if m.geom_bodyid[g] == bc]
    assert len(g_bc) == 10 and all(m.geom_contype[g] and m.geom_conaffinity[g] and m.geom_group[g] == 3 for g in g_bc)
    assert m.body_weldid[bc] == 0, "base_collision 이 world 고정 아님"
    excl = {(int(s) >> 16, int(s) & 0xFFFF) for s in m.exclude_signature}
    assert tuple(sorted((bc, sh))) in excl, "base_collision↔shoulder exclude 없음"
    d9 = mj.MjData(m)

    def base_hits():
        mj.mj_forward(m, d9)
        out = []
        for c in d9.contact[:d9.ncon]:
            b1, b2 = int(m.geom_bodyid[c.geom1]), int(m.geom_bodyid[c.geom2])
            if bc in (b1, b2):
                out.append((bn(b2 if b1 == bc else b1), float(c.dist)))
        return out

    pcb = twin._pcb_bid
    m.body_quat[pcb] = (1, 0, 0, 0)
    # (a) 강제 자세: pan 0, lift×elbow 13×13 × wrist_flex {하한,0,상한} 전 한계 안 격자 → 팔 링크↔base 관통 검출
    m.body_pos[pcb][:2] = (0.30, 0.0)
    arm_hit = {}
    for lift in np.linspace(lim[1, 0], lim[1, 1], 13):
        for elbow in np.linspace(lim[2, 0], lim[2, 1], 13):
            for wf in (lim[3, 0], 0.0, lim[3, 1]):
                d9.qpos[:6] = (0.0, lift, elbow, wf, 0.0, 0.0)
                for b, dist in base_hits():
                    if dist < -PENETRATION_TOL_M and b != "rs232_plug":
                        arm_hit[b] = min(arm_hit.get(b, 0.0), dist)
    assert "shoulder" not in arm_hit, "exclude 된 shoulder 가 base 와 접촉"
    assert arm_hit, "한계 안 강제 자세 507개에서 팔 링크↔base 관통 0 — base 충돌 비활성?"
    # (b) 후드↔base: PCB 를 존 밖 (0.0969, 0) 에 두면 후드 중심이 base 슬랩 안 → rs232_plug↔base 접촉. 정적 PCB·포트↔base 는 접촉 안 생김.
    d9.qpos[:6] = home
    m.body_pos[pcb][:2] = (0.0969, 0.0)
    hb = base_hits()
    hood_d = min((dist for b, dist in hb if b == "rs232_plug"), default=None)
    assert hood_d is not None and hood_d < -PENETRATION_TOL_M, f"후드↔base 접촉 미검출 {hb}"
    assert not any(b in ("pcb", "rs232_port", "rs232_port_2", "rs232_port_3") for b, _ in hb), hb
    # (c) HOME 자세 pan 전범위 201점 sweep (PCB 원거리) → base 와의 접촉 0 (shoulder 가짜 접촉 포함)
    m.body_pos[pcb][:2] = (0.30, 0.0)
    sweep = []
    for pan in np.linspace(lim[0, 0], lim[0, 1], 201):
        d9.qpos[:6] = home
        d9.qpos[0] = pan
        sweep += base_hits()
    assert not sweep, f"HOME pan sweep 에서 base 접촉 {sweep[:5]}"
    print(f"[9] base 충돌 활성 — geom 10(박스 8+메시 2) contype/group3, world 고정, exclude base_collision↔shoulder; "
          f"강제 자세 팔↔base 관통 {sorted((k, round(v*1e3, 1)) for k, v in arm_hit.items())} mm; "
          f"후드↔base {hood_d*1e3:.1f}mm (정적 PCB·포트↔base 접촉 0); HOME pan sweep 201점 base 접촉 0 (shoulder 포함)")

    # 11. HOME 중력 3초: 원래 자세 유지, 팔 관절 한계 제약 on/off 떨림 없음
    twin.reset(np.random.default_rng(7))
    n = int(3.0 / m.opt.timestep)
    q, active, qv_last = [], [], 0.0
    for k in range(n):
        twin.step()
        q.append(d.qpos[:6].copy())
        active.append(any(d.efc_type[i] == mj.mjtConstraint.mjCNSTR_LIMIT_JOINT and d.efc_id[i] < 6 for i in range(d.nefc)))
        if k >= n - int(1.0 / m.opt.timestep):
            qv_last = max(qv_last, float(np.abs(d.qvel[:6]).max()))
    dev = np.degrees(np.abs(np.array(q) - home).max(0))
    toggles = int(np.abs(np.diff(np.array(active, int))).sum())
    assert dev.max() < 0.5 and qv_last < 1e-3 and toggles == 0, f"HOME 불안정: 편차 {dev.round(3)}°, qvel {qv_last:.2e}, 한계 토글 {toggles}"
    print(f"[11] HOME 중력 3초 — 관절별 최대 편차 {dev.round(3).tolist()}°, 마지막 1초 |qvel| 최대 {qv_last:.1e} rad/s, "
          f"팔 관절 한계 제약 활성 스텝 {int(np.sum(active))}/{n}, on/off 토글 {toggles}")
    twin.close()
    print("sim_rs232_unplug 실기 정합 self-check: [8][9][11] PASS ([10][12] = check_vs_orig.py)")


if __name__ == "__main__":
    _self_check()
    _self_check_real()
