#!/usr/bin/env python3
"""RS232 파지 판별 가능성 검사 (로드맵 939 후속, 2026-10-03).

**결과부터: 기존 덤프로는 파지 타이밍 어긋남을 잴 수 없다.** 이 스크립트는 그것을 보인다.

2026-09-27 실패 분석이 지배적 실패를 NONPINCH 13/40 으로 규명하고 그 안의
'파지 타이밍 불일치' 10건을 지목했다. 어긋남의 크기(ms)를 재려 했으나,
판정이 쓰는 변수(후드 geom 과 양 jaw 의 동시 접촉)가 궤적 덤프에 **기록되지 않는다**.
남은 대리값은 그리퍼 관절각뿐인데, 아래 출력이 보이듯 그것으로는 파지를 분간할 수 없다.

입력: research/simulation/inference_progress/history/*_traj.json (per-frame qpos[0:6], 30fps)
출력: 표준출력 리포트 (파일 수정 없음, 재측정 없음 — 비파괴)

⚠ 두 가지 범위 한계를 결과와 함께 반드시 보고한다.

1. **시드 42 만.** 측정기는 traj 를 nominal 시드만 저장한다(`render_act_rollout_rs232.py`).
   40회 중 10회만 프레임 단위 분석이 가능하다.

2. **그리퍼 관절각은 접촉의 대리값(proxy)이다.** 판정이 쓰는 `pinched()` 는 후드 geom 이
   양 jaw 에 **동시 접촉**하는지를 본다. traj 에는 접촉이 없고 qpos 만 있다.
   따라서 '닫힘 구간'은 "집게가 닫힌 자세였던 구간"이지 "실제로 잡은 구간"이 아니다.
   닫혀 있어도 허공이면 파지가 아니다. 이 분석은 **상한**을 준다 — 닫힘 구간과
   임계 통과가 겹치지 않으면 파지도 확실히 겹치지 않는다. 역은 성립하지 않는다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HIST = ROOT / "research" / "simulation" / "inference_progress" / "history"

# 그리퍼 qpos 범위 — 측정 궤적에서 관측된 열림/닫힘 양끝 (web3d/playground 와 같은 상수)
GRIP_OPEN = 0.82
GRIP_CLOSED = 0.0
# 닫힘 판정: 열림 범위의 25% 이하까지 닫혔으면 '닫힘 자세'
CLOSE_THRESH = GRIP_CLOSED + 0.25 * (GRIP_OPEN - GRIP_CLOSED)
FPS = 30.0


def closed_intervals(frames: list[list[float]]) -> list[tuple[int, int]]:
    """그리퍼(qpos[5])가 닫힘 임계 이하인 연속 구간 [start, end] (프레임 인덱스, 양끝 포함)."""
    out: list[tuple[int, int]] = []
    start = None
    for i, f in enumerate(frames):
        closed = len(f) > 5 and f[5] <= CLOSE_THRESH
        if closed and start is None:
            start = i
        elif not closed and start is not None:
            out.append((start, i - 1))
            start = None
    if start is not None:
        out.append((start, len(frames) - 1))
    return out


def grip_at(frames: list[list[float]], pf: int | None) -> float | None:
    """임계 통과 프레임에서의 그리퍼 관절각 qpos[5]."""
    if pf is None or not (0 <= pf < len(frames)) or len(frames[pf]) < 6:
        return None
    return round(frames[pf][5], 3)


def analyze(traj_path: Path, summary_path: Path) -> dict:
    traj = json.loads(traj_path.read_text())
    summ = json.loads(summary_path.read_text())
    by_idx = {r["rollout"]: r for r in summ["results"]}

    rows = []
    for r in traj["rollouts"]:
        i = r["rollout"]
        s = by_idx.get(i, {})
        frames = r.get("frames") or []
        pf = r.get("partial_frame")
        iv = closed_intervals(frames)
        rows.append({
            "rollout": i,
            "success": s.get("success"),
            "full": s.get("full_success"),
            "legacy": s.get("success_nopinch"),
            "disp_mm": s.get("max_disp_mm"),
            "pinch_steps": s.get("pinch_steps"),
            "partial_frame": pf,
            "n_closed": len(iv),
            "closed_frames": sum(b - a + 1 for a, b in iv),
            "grip_at_cross": grip_at(frames, pf),
        })
    return {"checkpoint": summ.get("checkpoint"), "seed": summ.get("seed"),
            "measured_at": summ.get("measured_at"), "rows": rows}


def classify(r: dict) -> str:
    """2026-09-27 분류와 같은 기준 (단 여기서는 시드42 10회 한정)."""
    if r["success"]:
        return "SUCCESS"
    if r["legacy"]:                       # 변위는 임계를 넘었는데 핀치 판정 탈락
        return "NONPINCH-pure" if not r["pinch_steps"] else "NONPINCH-timing"
    return "SHORT"


def report(res: dict) -> None:
    print(f"\n{'='*78}")
    print(f"체크포인트 {res['checkpoint']}  시드 {res['seed']}  측정 {res['measured_at'][:19]}")
    print(f"{'='*78}")
    print(f"{'#':>2} {'유형':<15} {'변위mm':>7} {'파지步':>6} {'임계프레임':>8} {'임계시점 qpos[5]':>15}")
    print("-" * 78)
    agg: dict[str, list[float]] = {}
    for r in res["rows"]:
        c = classify(r)
        g = r["grip_at_cross"]
        print(f"{r['rollout']:>2} {c:<15} {r['disp_mm']:>7} {r['pinch_steps']:>6} "
              f"{str(r['partial_frame']):>8} {('-' if g is None else f'{g:.3f}'):>15}")
        if g is not None:
            agg.setdefault(c, []).append(g)
    print("-" * 78)
    for c, v in sorted(agg.items()):
        print(f"  {c:<15} n={len(v):<3} qpos[5] 범위 {min(v):.3f} ~ {max(v):.3f}")
    grasp = [g for r, g in ((r, r["grip_at_cross"]) for r in res["rows"])
             if g is not None and (r["pinch_steps"] or 0) > 0]
    nograsp = [g for r, g in ((r, r["grip_at_cross"]) for r in res["rows"])
               if g is not None and not (r["pinch_steps"] or 0)]
    if grasp and nograsp:
        print(f"\n  ⚠ 판별 불가 — 한 번이라도 파지한 롤아웃 {min(grasp):.3f}~{max(grasp):.3f} vs "
              f"한 번도 못 잡은 롤아웃 {min(nograsp):.3f}~{max(nograsp):.3f}")
        print(f"     두 집단의 임계시점 집게 각도가 겹치거나 {abs(min(nograsp)-max(grasp)):.3f} rad 밖에 안 떨어진다.")
        print("     관절각으로는 파지 여부를 분간할 수 없다 — 판별 변수는 접촉이고, 접촉은 기록되지 않는다.")


def main() -> int:
    pairs = [
        ("20260918-230214_act_rs232_sim_epoch_0041", "공칭 (공표 0.600)"),
        ("20260926-230231_act_rs232_sim_epoch_0041", "DR-trained (0.425) — 파일명은 _sim 이나 내용은 DR"),
    ]
    for stem, label in pairs:
        t, s = HIST / f"{stem}_traj.json", HIST / f"{stem}.json"
        if not (t.exists() and s.exists()):
            print(f"[건너뜀] {label}: {stem} 없음")
            continue
        print(f"\n### {label}")
        report(analyze(t, s))
    print("\n" + "=" * 78)
    print("결론")
    print("  파지 타이밍 어긋남은 기존 덤프로 **측정 불가**다. 판정이 쓰는 변수는 후드 geom 과")
    print("  양 jaw 의 동시 접촉인데 궤적 덤프에는 qpos 만 있고 접촉이 없다. 유일한 대리값인")
    print("  그리퍼 관절각은 위 출력대로 파지/비파지를 분간하지 못한다.")
    print("")
    print("  재려면 측정기가 per-step 파지 상태를 기록해야 한다 —")
    print("  scripts/render_act_rollout_rs232.py 의 루프에서 pin_now 를 프레임별로 모아")
    print("  traj 에 함께 저장하면 된다(기존 pinch_steps 는 합계만 남긴다).")
    print("  이는 **새 측정을 요구**하므로 10월 기준선 동결 중에는 하지 않는다. 이후로 이관.")
    print("")
    print("범위 한계")
    print("  시드 42 만 — traj 는 nominal 시드만 저장된다. 40회 중 10회.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
