#!/usr/bin/env python3
"""site-docs 스크린샷 캡쳐 — hdel·cop 공유 (byte-identical). SP2.

빌드된 dashboard.html 을 로컬 서빙 → gstack browse(헤드리스)로 각 page 뷰 캡쳐 →
dashboard/screenshots/<file> + manifest.json(ui_hash). 대표 스냅샷: ui_hash 변경분만 재캡쳐.
사용: python3 dashboard/capture_screenshots.py [--force] [--only <id>]
"""
from __future__ import annotations
import argparse, contextlib, functools, hashlib, http.server, json, os, socket, socketserver, subprocess, sys, tempfile, threading, time
from datetime import datetime, timezone
from pathlib import Path

DASH = Path(__file__).resolve().parent           # dashboard/
SHOTS = DASH / "screenshots"
PAGES = DASH / "content" / "pages"
DASHBOARD_HTML = DASH / "dashboard.html"


def browse_bin() -> str:
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    for c in [f"{root}/.claude/skills/gstack/browse/dist/browse", f"{Path.home()}/.claude/skills/gstack/browse/dist/browse"]:
        if c and os.access(c, os.X_OK):
            return c
    sys.exit("browse 바이너리 없음 — `cd ~/.claude/skills/gstack/browse && ./setup` 필요")


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    meta: dict[str, str] = {}
    for raw in parts[1].splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        meta[k.strip()] = v
    return meta


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def serve(directory: Path, port: int) -> socketserver.TCPServer:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def browse(b: str, *args: str) -> str:
    return subprocess.run([b, *args], capture_output=True, text=True).stdout


def js_out(b: str, expr: str) -> str:
    """browse js --out --raw 로 결과를 임시파일에 받아 마커 오염 없이 읽음."""
    # browse --out 는 /tmp 또는 cwd 스코프만 허용 (macOS $TMPDIR=/var/folders 는 거부됨).
    with tempfile.NamedTemporaryFile("r", suffix=".txt", delete=False, dir="/tmp") as tf:
        path = tf.name
    browse(b, "js", expr, "--out", path, "--raw")
    try:
        return Path(path).read_text(encoding="utf-8")
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="ui_hash 무관 전체 재캡쳐")
    ap.add_argument("--only", help="해당 id 만 캡쳐")
    args = ap.parse_args()

    if not DASHBOARD_HTML.is_file():
        subprocess.run(["python3", str(DASH / "build.py")], check=True)
    SHOTS.mkdir(exist_ok=True)
    manifest_path = SHOTS / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}

    b = browse_bin()
    port = free_port()
    httpd = serve(DASH, port)
    try:
        browse(b, "goto", f"http://127.0.0.1:{port}/dashboard.html")
        browse(b, "wait", "--load")
        css_text = js_out(b, "[...document.querySelectorAll('style')].map(s=>s.textContent).join('')")
        css_hash = hashlib.sha256(css_text.encode("utf-8")).hexdigest()

        captured, skipped, failed = [], [], []
        for fp in sorted(PAGES.glob("*.md")):
            meta = parse_frontmatter(fp.read_text(encoding="utf-8"))
            sid = meta.get("id", fp.stem)
            fname = meta.get("screenshot", "")
            route = meta.get("menu_route", sid)
            if not fname:
                continue
            if args.only and sid != args.only:
                continue
            sel = f"#view-{route}"
            view_html = js_out(b, f"(document.getElementById('view-{route}')||{{}}).outerHTML||''")
            if not view_html:
                failed.append(f"{sid} (뷰 #{sel} 없음)")
                continue
            ui_hash = hashlib.sha256((css_hash + "\x00" + view_html).encode("utf-8")).hexdigest()
            png = SHOTS / fname
            if not args.force and png.is_file() and manifest.get(sid, {}).get("ui_hash") == ui_hash:
                skipped.append(sid)
                continue
            # 뷰 진입 + capture_steps 실행
            browse(b, "js", f"setRoute('{route}')")
            for step in (meta.get("capture_steps", "") or "").split("|"):
                step = step.strip()
                if not step:
                    continue
                verb, _, rest = step.partition(" ")
                rest = rest.strip()
                if verb == "click":
                    browse(b, "click", rest)
                elif verb == "wait":
                    browse(b, "wait", rest)
                elif verb == "eval":
                    browse(b, "js", rest)
                else:
                    print(f"  ! 알 수 없는 capture_step: {step}", file=sys.stderr)
            time.sleep(0.4)  # 렌더 안정화
            browse(b, "screenshot", str(png), "--selector", sel)
            manifest[sid] = {"ui_hash": ui_hash, "captured_at": datetime.now(timezone.utc).isoformat()}
            captured.append(sid)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"캡쳐 {len(captured)}: {captured} | skip {len(skipped)} | 실패 {failed}")
        return 1 if failed else 0
    finally:
        httpd.shutdown()
        browse(b, "stop")


if __name__ == "__main__":
    raise SystemExit(main())
