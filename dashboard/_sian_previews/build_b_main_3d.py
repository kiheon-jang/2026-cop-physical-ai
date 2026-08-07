#!/usr/bin/env python3
"""Assemble B_main_3d.html — self-contained hero-3D preview.
Injects three.r152.js + REAL_TRAJ + WEB3D_CHAIN + arm3d.js into B_main_v2.html markers.
Run: python3 build_b_main_3d.py
"""
import pathlib

HERE = pathlib.Path(__file__).parent
DASH = HERE.parent

src   = (HERE / "B_main_v2.html").read_text()
three = (HERE / "three.r152.js").read_text()
traj  = (HERE / "real_traj_full.json").read_text().strip()
chain = (DASH / "web3d_chain.json").read_text().strip()
arm   = (HERE / "arm3d.js").read_text()

INJ = {
    "<!--INJECT:THREEJS-->": f"<script>\n{three}\n</script>",
    "<!--INJECT:REALTRAJ-->": (
        "<script>\n"
        f"window.REAL_TRAJ={traj};\n"
        f"window.WEB3D_CHAIN={chain};\n"
        "</script>"
    ),
    "<!--INJECT:ARM3D-->": f"<script>\n{arm}\n</script>",
}

out = src
for marker, payload in INJ.items():
    assert marker in out, f"marker missing: {marker}"
    out = out.replace(marker, payload)

dst = HERE / "B_main_3d.html"
dst.write_text(out)
print(f"wrote {dst} ({len(out)/1024:.0f} KB)")
