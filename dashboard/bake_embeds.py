#!/usr/bin/env python3
"""시안 C(스토리)·D(플레이그라운드) 자립형 HTML 을 template.html 의 iframe srcdoc 에 베이크한다.

배경: hermes-mark 서버가 template.html 을 직접 서빙하고 build.py 산출물(dashboard.html)은
서빙하지 않는다. 따라서 build.py 의 마커 주입만으론 서버뷰(스토리/플레이그라운드)가 빈 화면이 된다.
→ C/D 내용을 template.html 소스에 직접 구워 서버가 그대로 내보내게 한다.

C_scrolly.html / D_playground.html 을 수정하면 이 스크립트를 재실행해 다시 굽는다:
    .venv/bin/python3 dashboard/bake_embeds.py
(arm3d.js 는 template 에 이미 인라인됨 — 별도.)
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
TPL = ROOT / "template.html"


def esc_attr(x: str) -> str:
    # 큰따옴표 속성값 안이므로 & 와 " 만 이스케이프
    return x.replace("&", "&amp;").replace('"', "&quot;")


def main() -> int:
    s = TPL.read_text(encoding="utf-8")
    for frame_id, fname in (("story-frame", "C_scrolly.html"),
                            ("playground-frame", "D_playground.html")):
        content = esc_attr((ROOT / "_sian_previews" / fname).read_text(encoding="utf-8"))
        # 해당 iframe 의 data-srcdoc="..." 값을 통째로 교체 (마커든 이전 베이크든 [^"]* 로 매칭).
        pat = re.compile(r'(id="' + re.escape(frame_id) + r'"[^>]*?data-srcdoc=")[^"]*(")',
                         re.DOTALL)
        s, n = pat.subn(lambda m: m.group(1) + content + m.group(2), s, count=1)
        if n != 1:
            raise SystemExit(f"베이크 실패: {frame_id} data-srcdoc 매칭 {n}건 (1 기대)")
    TPL.write_text(s, encoding="utf-8")
    print("baked C/D into template.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
