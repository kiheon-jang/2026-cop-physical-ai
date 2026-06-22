"""가동조 평평 패드의 moving_jaw body 로컬 pos/quat/size 계산.
그리퍼 프레임에서 정의한 패드(안쪽면 x=+0.0194, band z=-0.085)를 q=0.195 자세에서
moving_jaw 프레임으로 변환 → 그 body에 box geom 으로 붙인다.
"""
import mujoco, numpy as np

m = mujoco.MjModel.from_xml_path("SO-ARM100/Simulation/SO101/scene_grasp_pads.xml")
d = mujoco.MjData(m)
nid = lambda t, n: mujoco.mj_name2id(m, t, n)
GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")
JBID = nid(mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
GQA = m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, "gripper")]
d.qpos[:] = 0; d.qpos[GQA] = 0.195
mujoco.mj_forward(m, d)

gx = d.xpos[GBID]; gR = d.xmat[GBID].reshape(3, 3)
jx = d.xpos[JBID]; jR = d.xmat[JBID].reshape(3, 3)

# 그리퍼 프레임 패드 스펙: 가동 안쪽(-x)면이 +0.0194, 두께 4mm → 중심 x=+0.0234
SIZE = np.array([0.004, 0.012, 0.018])
center_grip = np.array([0.0234, -0.0002, -0.085])
world_center = gx + gR @ center_grip
center_jaw = jR.T @ (world_center - jx)
R_rel = jR.T @ gR   # 그리퍼축 정렬 박스를 jaw 프레임에서 표현하는 회전
quat = np.zeros(4); mujoco.mju_mat2Quat(quat, R_rel.flatten())
print("가동 패드 geom (moving_jaw body):")
print(f'  pos="{center_jaw[0]:.5f} {center_jaw[1]:.5f} {center_jaw[2]:.5f}"')
print(f'  quat="{quat[0]:.6f} {quat[1]:.6f} {quat[2]:.6f} {quat[3]:.6f}"')
print(f'  size="{SIZE[0]} {SIZE[1]} {SIZE[2]}"')
# 검증: 이 박스의 안쪽(-x)면 중심을 다시 그리퍼 프레임으로
inner_face_grip = center_grip + np.array([-SIZE[0], 0, 0])
print(f"  검증: 안쪽면 그리퍼-x = {inner_face_grip[0]:+.4f} (목표 +0.0194)")
