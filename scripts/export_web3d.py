#!/Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv/bin/python
"""
웹 3D 리플레이용 키네마틱 체인 + 경량 메시 내보내기.

MuJoCo 모델(scene_grasp_pads.xml — 학습/측정과 동일 씬)에서 직접 추출:
  - body 트리 (local pos/quat) + hinge 조인트 (axis/anchor/qpos 주소)
  - geom (mesh 참조 + primitive box/plane) + rgba
  - mesh 정점/면 → 정점 클러스터링 데시메이션 → base64(Float32/Uint32)

출력: dashboard/web3d_chain.json  (build.py 가 data.json 에 임베드)
대시보드 JS 가 이 체인으로 FK 를 계산해 qpos6 궤적(수집 에피소드/정책 rollout)을 재생한다.
씬이 바뀌지 않는 한 1회 실행이면 충분 (커밋 대상).

사용:  .venv/bin/python3 scripts/export_web3d.py [--max-faces 6000]
"""

import argparse
import base64
import json
from pathlib import Path

import numpy as np

ROOT = Path("/Volumes/MARK_DATA/dev/2026-cop-physical-ai")
MODEL_XML = ROOT / "SO-ARM100" / "Simulation" / "SO101" / "scene_grasp_pads.xml"
OUT = ROOT / "dashboard" / "web3d_chain.json"


def decimate(verts: np.ndarray, faces: np.ndarray, max_faces: int) -> tuple[np.ndarray, np.ndarray]:
    """정점 클러스터링 데시메이션 (외부 의존 없음). max_faces 이하가 될 때까지 셀 확대."""
    if len(faces) <= max_faces:
        return verts, faces
    bbox = verts.max(0) - verts.min(0)
    diag = float(np.linalg.norm(bbox)) or 1e-6
    cell = diag / 80.0
    for _ in range(12):
        keys = np.floor((verts - verts.min(0)) / cell).astype(np.int64)
        _, inverse, counts = np.unique(keys, axis=0, return_inverse=True, return_counts=True)
        new_verts = np.zeros((len(counts), 3), dtype=np.float64)
        np.add.at(new_verts, inverse, verts)
        new_verts /= counts[:, None]
        f = inverse[faces]
        keep = (f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])
        f = f[keep]
        # 중복 face 제거
        f_sorted = np.sort(f, axis=1)
        _, uniq_idx = np.unique(f_sorted, axis=0, return_index=True)
        f = f[np.sort(uniq_idx)]
        if len(f) <= max_faces:
            return new_verts, f
        cell *= 1.5
    return new_verts, f


def b64_f32(a: np.ndarray) -> str:
    return base64.b64encode(np.ascontiguousarray(a, dtype=np.float32).tobytes()).decode()


def b64_u32(a: np.ndarray) -> str:
    return base64.b64encode(np.ascontiguousarray(a, dtype=np.uint32).tobytes()).decode()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-faces", type=int, default=6000, help="mesh 당 최대 face 수")
    args = ap.parse_args()

    import mujoco

    model = mujoco.MjModel.from_xml_path(str(MODEL_XML))

    def name(objtype, i):
        return mujoco.mj_id2name(model, objtype, i) or f"{objtype}_{i}"

    bodies = []
    for b in range(model.nbody):
        bodies.append({
            "id": b,
            "name": name(mujoco.mjtObj.mjOBJ_BODY, b),
            "parent": int(model.body_parentid[b]),
            "pos": [round(float(x), 6) for x in model.body_pos[b]],
            "quat": [round(float(x), 6) for x in model.body_quat[b]],  # (w,x,y,z)
        })

    joints = []
    for j in range(model.njnt):
        jtype = int(model.jnt_type[j])
        joints.append({
            "id": j,
            "name": name(mujoco.mjtObj.mjOBJ_JOINT, j),
            "body": int(model.jnt_bodyid[j]),
            "type": {0: "free", 1: "ball", 2: "slide", 3: "hinge"}[jtype],
            "pos": [round(float(x), 6) for x in model.jnt_pos[j]],
            "axis": [round(float(x), 6) for x in model.jnt_axis[j]],
            "qposadr": int(model.jnt_qposadr[j]),
            "range": [round(float(x), 4) for x in model.jnt_range[j]],
        })

    used_meshes: dict[int, str] = {}
    geoms = []
    for g in range(model.ngeom):
        gtype = int(model.geom_type[g])
        # 색: geom rgba 가 기본값(0.5 회색)이고 material 이 지정돼 있으면 material rgba 사용
        # (MuJoCo 는 material 색을 geom_rgba 에 복사하지 않는다 — 받침대 갈색 등이 소실됨)
        rgba = [round(float(x), 3) for x in model.geom_rgba[g]]
        matid = int(model.geom_matid[g])
        if matid >= 0 and rgba == [0.5, 0.5, 0.5, 1.0]:
            rgba = [round(float(x), 3) for x in model.mat_rgba[matid]]
        entry = {
            "name": name(mujoco.mjtObj.mjOBJ_GEOM, g),
            "body": int(model.geom_bodyid[g]),
            "type": {0: "plane", 2: "sphere", 3: "capsule", 5: "cylinder", 6: "box", 7: "mesh"}.get(gtype, f"t{gtype}"),
            "pos": [round(float(x), 6) for x in model.geom_pos[g]],
            "quat": [round(float(x), 6) for x in model.geom_quat[g]],
            "size": [round(float(x), 6) for x in model.geom_size[g]],
            "rgba": rgba,
            "group": int(model.geom_group[g]),
        }
        if gtype == mujoco.mjtGeom.mjGEOM_MESH:
            mid = int(model.geom_dataid[g])
            entry["mesh"] = name(mujoco.mjtObj.mjOBJ_MESH, mid)
            used_meshes[mid] = entry["mesh"]
        geoms.append(entry)

    meshes = {}
    total_faces = 0
    for mid, mname in used_meshes.items():
        va, vn = int(model.mesh_vertadr[mid]), int(model.mesh_vertnum[mid])
        fa, fn = int(model.mesh_faceadr[mid]), int(model.mesh_facenum[mid])
        verts = model.mesh_vert[va:va + vn].astype(np.float64)
        faces = model.mesh_face[fa:fa + fn].astype(np.int64)
        dverts, dfaces = decimate(verts, faces, args.max_faces)
        total_faces += len(dfaces)
        meshes[mname] = {
            "verts_b64": b64_f32(dverts),
            "faces_b64": b64_u32(dfaces),
            "n_verts": len(dverts),
            "n_faces": len(dfaces),
            "orig_faces": fn,
        }

    payload = {
        "source": str(MODEL_XML.relative_to(ROOT)),
        "nq": int(model.nq),
        "bodies": bodies,
        "joints": joints,
        "geoms": geoms,
        "meshes": meshes,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    size_kb = OUT.stat().st_size / 1024
    print(json.dumps({
        "out": str(OUT.relative_to(ROOT)),
        "bodies": len(bodies), "joints": len(joints), "geoms": len(geoms),
        "meshes": len(meshes), "total_faces": total_faces,
        "size_kb": round(size_kb, 1),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
