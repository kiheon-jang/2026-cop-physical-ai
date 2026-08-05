"""Phase 3 W1 — S1 리셋버튼 트윈 (실기 정렬).

실기 트랙(soarm_lerobot) soarm/sim/twin.py 를 이식·확장한다:
  1. 눌림 판정 = 접촉이 아니라 **슬라이드 조인트 변위 임계** (실제로 눌려야 성공)
  2. LED latch = 한 번 눌리면 점등 유지 → 에피소드 성공의 공짜 정답 라벨
     (실기 P1 녹색 LED 판정과 동일 계약 — 시뮬에선 판정기가 필요 없다)
  3. 15×15cm 존 배치 무작위화 reset 훅 (실기 spec 의 "제한 가변 위치" 그대로)
  4. top / closeup 640×480 렌더 — 실기 관측 스키마(observation.images.{top,closeup})와 동일 이름

W2 에서 closed-loop expert + 수집기가 이 모듈을 import 한다.
headless 전용 (mujoco.Renderer). viewer 호출 없음.
"""
import os
import numpy as np
import mujoco as mj

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCENE_PATH = os.path.join(BASE, "sim/assets/pcb_reset_scene.xml")

# 실기 정렬 계약 (soarm_lerobot soarm/config.py 와 동일해야 한다)
CAM_W, CAM_H = 640, 480
FPS = 30
TASK_LABEL = "press the reset button"
CAMERA_NAMES = ("top", "closeup")

# 버튼 트래블 3mm 중 절반 이상 들어가야 "눌림"
PRESS_THRESHOLD = -0.0015

# PCB 배치 존: 15×15cm (실기 spec "제한 가변 위치"), 방향은 대체로 정면(±10°)
ZONE_X = (0.15, 0.30)
ZONE_Y = (-0.075, 0.075)
ZONE_YAW_DEG = 10.0

# 에피소드 시작 홈 자세 — 팔을 뒤로 접어 top 카메라에서 PCB 존이 가려지지 않게
# (실기 C920 뷰 = "PCB 전체 + 팔 베이스"와 동일 구도. 육안 검증 2026-08-05)
HOME_QPOS = (0.0, -1.6, 1.4, 0.9, 0.0, 0.0)

LED_ON_RGBA = (0.1, 0.9, 0.1, 1.0)
LED_OFF_RGBA = (0.2, 0.2, 0.2, 1.0)


class PcbResetTwin:
    def __init__(self, scene_path: str = SCENE_PATH):
        self.model = mj.MjModel.from_xml_path(scene_path)
        self.data = mj.MjData(self.model)
        self._led_gid = self._gid("led_geom")
        self._pcb_bid = mj.mj_name2id(self.model, mj.mjtObj.mjOBJ_BODY, "pcb")
        jid = mj.mj_name2id(self.model, mj.mjtObj.mjOBJ_JOINT, "reset_button_slide")
        self._btn_qadr = self.model.jnt_qposadr[jid]
        self._pressed_latch = False
        self._renderer = None

    def _gid(self, name):
        return mj.mj_name2id(self.model, mj.mjtObj.mjOBJ_GEOM, name)

    # ── 에피소드 리셋 + 존 무작위화 ────────────────────────────────────────
    def reset(self, rng: np.random.Generator | None = None) -> dict:
        """mj_resetData + (rng 주면) PCB 를 15×15cm 존 안에 재배치. 배치 dict 반환."""
        mj.mj_resetData(self.model, self.data)
        self._pressed_latch = False
        self.data.qpos[:6] = HOME_QPOS
        self.data.ctrl[:6] = HOME_QPOS  # position 서보 — step 중 홈 자세 유지
        placement = {"x": None, "y": None, "yaw_deg": 0.0}
        if rng is not None:
            x = float(rng.uniform(*ZONE_X))
            y = float(rng.uniform(*ZONE_Y))
            yaw = float(rng.uniform(-ZONE_YAW_DEG, ZONE_YAW_DEG))
            self.model.body_pos[self._pcb_bid][:2] = (x, y)
            half = np.deg2rad(yaw) / 2.0
            self.model.body_quat[self._pcb_bid] = (np.cos(half), 0, 0, np.sin(half))
            placement = {"x": x, "y": y, "yaw_deg": yaw}
        self._set_led(False)
        mj.mj_forward(self.model, self.data)
        return placement

    # ── 버튼 / LED ────────────────────────────────────────────────────────
    def button_pressed(self) -> bool:
        return float(self.data.qpos[self._btn_qadr]) <= PRESS_THRESHOLD

    def led_on(self) -> bool:
        return self._pressed_latch

    def _set_led(self, on: bool):
        self.model.geom_rgba[self._led_gid] = LED_ON_RGBA if on else LED_OFF_RGBA

    def step(self):
        mj.mj_step(self.model, self.data)
        if self.button_pressed() and not self._pressed_latch:
            self._pressed_latch = True
            self._set_led(True)

    # ── 렌더 (실기 관측 스키마와 동일 카메라 이름) ─────────────────────────
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


def _self_check():  # noqa: C901
    """W1 완료 기준 자가검증 — 씬 로드 / 눌림 메커니즘 / 존 무작위화 / 2카메라 렌더."""
    twin = PcbResetTwin()
    m, d = twin.model, twin.data

    # 1. 로드: 팔 6축 + 버튼 조인트, 카메라 2대
    assert m.nu == 6, f"actuator 6 기대, {m.nu}"
    for cam in CAMERA_NAMES:
        assert mj.mj_name2id(m, mj.mjtObj.mjOBJ_CAMERA, cam) >= 0, f"camera '{cam}' 없음"

    # 2. 존 무작위화: 결정론(같은 seed 같은 배치) + 존 경계 준수
    p1 = twin.reset(np.random.default_rng(42))
    p2 = twin.reset(np.random.default_rng(42))
    assert p1 == p2, "seed 42 재현 실패"
    for _ in range(50):
        p = twin.reset(np.random.default_rng())
        assert ZONE_X[0] <= p["x"] <= ZONE_X[1] and ZONE_Y[0] <= p["y"] <= ZONE_Y[1], p
        assert abs(p["yaw_deg"]) <= ZONE_YAW_DEG

    # 3. 눌림 메커니즘: 변위 임계 도달 → latch, 스프링 복원 후에도 latch 유지
    twin.reset(np.random.default_rng(7))
    assert not twin.button_pressed() and not twin.led_on()
    d.qpos[twin._btn_qadr] = -0.003          # 풀 스트로크로 누름
    twin.step()
    assert twin.led_on(), "눌림 latch 실패"
    for _ in range(300):                      # 스프링이 버튼을 되돌린다
        twin.step()
    assert d.qpos[twin._btn_qadr] > PRESS_THRESHOLD, \
        f"스프링 복원 실패: qpos={d.qpos[twin._btn_qadr]:.5f}"
    assert twin.led_on(), "latch 가 복원 중에 풀렸다"
    assert tuple(m.geom_rgba[twin._led_gid][:3]) == LED_ON_RGBA[:3], "LED rgba 미반영"

    # 4. 렌더: 두 카메라 640×480, 내용 있는 프레임(상수 이미지 아님)
    for cam in CAMERA_NAMES:
        img = twin.render(cam)
        assert img.shape == (CAM_H, CAM_W, 3), img.shape
        assert float(img.std()) > 5.0, f"{cam} 렌더가 비어 있음 (std={img.std():.2f})"

    twin.close()
    print("sim_pcb_reset self-check: 4/4 PASS "
          f"(카메라 {CAMERA_NAMES}, 존 {ZONE_X}×{ZONE_Y}, 임계 {PRESS_THRESHOLD}m)")


if __name__ == "__main__":
    _self_check()
