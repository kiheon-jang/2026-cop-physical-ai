#!/usr/bin/env python3
"""template.html 에 arm3d.js(3D 팔) 인라인 + 시안 C(스토리)를 iframe srcdoc 에 베이크한다.

배경: hermes-mark 서버가 template.html 을 직접 서빙하고 build.py 산출물(dashboard.html)은
서빙하지 않는다. build.py 마커 주입만으론 서버뷰가 빈 화면이 되므로 여기서 직접 굽는다.
arm3d.js / C_scrolly.html 을 수정하면 이 스크립트를 재실행:
    .venv/bin/python3 dashboard/bake_embeds.py

Playground(플레이그라운드)는 iframe 이 아니라 native 3D(#play3d, mountArm3D)로 바뀌어 D_playground 는
더 이상 임베드하지 않는다.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
TPL = ROOT / "template.html"


def esc_attr(x: str) -> str:
    return x.replace("&", "&amp;").replace('"', "&quot;")


def main() -> int:
    s = TPL.read_text(encoding="utf-8")

    # 1) arm3d.js 인라인 (마커 → 실제 코드). 마커 없으면(이미 인라인) 스킵.
    arm3d = (ROOT / "_sian_previews" / "arm3d.js").read_text(encoding="utf-8")
    if "/*__ARM3D_JS__*/" in s:
        s = s.replace("/*__ARM3D_JS__*/", arm3d, 1)
        print("arm3d.js inlined")
    else:
        print("arm3d marker 없음 — 스킵(이미 인라인?)")

    # 2) 스토리(C) 를 story-frame iframe srcdoc 에 베이크
    import re
    content = esc_attr((ROOT / "_sian_previews" / "C_scrolly.html").read_text(encoding="utf-8"))
    pat = re.compile(r'(id="story-frame"[^>]*?data-srcdoc=")[^"]*(")', re.DOTALL)
    s, n = pat.subn(lambda m: m.group(1) + content + m.group(2), s, count=1)
    if n != 1:
        raise SystemExit(f"베이크 실패: story-frame data-srcdoc 매칭 {n}건 (1 기대)")
    print("C(스토리) baked into story-frame")

    # 3) 왜 피지컬 AI인가 를 whypai-frame iframe srcdoc 에 베이크
    why = ROOT / "_sian_previews" / "WHYPAI.html"
    if why.exists():
        wc = esc_attr(why.read_text(encoding="utf-8"))
        wpat = re.compile(r'(id="whypai-frame"[^>]*?data-srcdoc=")[^"]*(")', re.DOTALL)
        s, wn = wpat.subn(lambda m: m.group(1) + wc + m.group(2), s, count=1)
        if wn != 1:
            raise SystemExit(f"베이크 실패: whypai-frame data-srcdoc 매칭 {wn}건 (1 기대)")
        print("WHYPAI(왜 피지컬 AI인가) baked into whypai-frame")

    TPL.write_text(s, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
