#!/usr/bin/env python3
"""RS232 unplug 실패 케이스 분해 (로드맵 939 시뮬 실패 케이스 분석).

배포 모델(nominal act_rs232_sim/epoch_0041, 9/18 4-seed 측정 = 부분성공 0.600)의
40 rollout 을 per-rollout 덤프에서 읽어 실패를 유형 분류한다.

유형:
  SUCCESS      — 핀치 부분성공 (success=True)
  UNREACH      — 근단 도달불가: pcb.x < X_NEAR 이고 변위 < partial 임계 (shoulder 기하 상한)
  NONPINCH     — 비핀치 밀고끌기: 변위 >= partial 임계인데 핀치 안 함 (legacy 는 성공으로 셈)
  SHORT        — 도달했으나 변위 부족: x >= X_NEAR, 변위 < partial 임계, 핀치 무관

배치 의존성(seed 마다 실패 rollout 이 이동 = 모방격차) 도 함께 집계한다.

사용: .venv/bin/python3 scripts/analyze_rs232_failures.py [--dr]
      --dr 는 DR-trained(9/26) 비교 arm 을 대신 분석.
"""
import argparse
import glob
import json
import os

HIST = os.path.join(os.path.dirname(__file__), "..",
                    "research/simulation/inference_progress/history")
X_NEAR = 0.19  # 존 근단 경계 (로드맵: x<0.19 도달불가 shoulder 기하 상한 ~37.5%)

# 배포 모델(nominal) = 9/18, DR 비교 arm = 9/26
NOMINAL_PREFIX = "20260918-230214"  # seed42 main; 형제 seed7/123/2026 동시각
DR_PREFIX = "20260926-230231"


def load_seed_set(prefix):
    """한 측정 세션의 4-seed 요약 파일 4개를 로드."""
    base = os.path.join(HIST, prefix + "_act_rs232_sim_epoch_0041")
    files = [base + ".json"]  # seed42
    # 형제 seed 파일은 같은 날짜 다른 시각 → glob 로 seed7/123/2026 수집
    day = prefix.split("-")[0]
    for s in ("seed7", "seed123", "seed2026"):
        m = sorted(glob.glob(os.path.join(HIST, f"{day}-*_act_rs232_sim_epoch_0041_{s}.json")))
        assert m, f"missing {s} for {day}"
        files.append(m[-1])
    return [json.load(open(f)) for f in files]


def classify(r, partial_mm):
    if r["success"]:
        return "SUCCESS"
    x = r["pcb"]["x"]
    disp = r["max_disp_mm"]
    if disp >= partial_mm:
        # 임계 넘게 움직였는데 success=False → 핀치 실패 (밀고끌기)
        return "NONPINCH"
    if x < X_NEAR:
        return "UNREACH"
    return "SHORT"


def analyze(prefix, label):
    summ = load_seed_set(prefix)
    partial_mm = summ[0]["partial_threshold_mm"]
    cats = {"SUCCESS": 0, "UNREACH": 0, "NONPINCH": 0, "SHORT": 0}
    fail_by_seed = {}
    near_total = near_fail = 0
    per_seed_sr = {}
    for s in summ:
        seed = s["seed"]
        fails = []
        for r in s["results"]:
            c = classify(r, partial_mm)
            cats[c] += 1
            if r["pcb"]["x"] < X_NEAR:
                near_total += 1
                if not r["success"]:
                    near_fail += 1
            if c != "SUCCESS":
                fails.append((r["rollout"], c, round(r["pcb"]["x"], 3),
                              round(r["max_disp_mm"], 2), r["pinch_steps"]))
        fail_by_seed[seed] = fails
        per_seed_sr[seed] = s["success_rate"]
    n = sum(cats.values())
    print(f"\n===== {label} (partial 임계 {partial_mm}mm, X_NEAR {X_NEAR}) =====")
    print(f"총 rollout: {n}  성공률(부분/핀치): {cats['SUCCESS']}/{n} = {cats['SUCCESS']/n:.3f}")
    print(f"seed별 성공률: {per_seed_sr}")
    print("실패 유형 분해:")
    for c in ("UNREACH", "NONPINCH", "SHORT"):
        print(f"  {c:9s}: {cats[c]:2d}/{n}  ({cats[c]/n:.1%})")
    print(f"근단(x<{X_NEAR}) rollout: {near_total}개 중 실패 {near_fail}개 "
          f"(근단 실패율 {near_fail/near_total:.1%})" if near_total else "근단 rollout 0")
    print("실패 rollout (seed → [rollout,유형,x,disp_mm,pinch_steps]):")
    for seed, fails in fail_by_seed.items():
        ids = [f[0] for f in fails]
        print(f"  seed {seed}: {ids}")
        for f in fails:
            print(f"      r{f[0]}: {f[1]:9s} x={f[2]:.3f} disp={f[3]:.2f}mm pinch={f[4]}")
    # 배치 의존: 실패 rollout 인덱스가 seed 간 겹치는지
    sets = [set(f[0] for f in fails) for fails in fail_by_seed.values()]
    common = set.intersection(*sets) if sets else set()
    union = set.union(*sets) if sets else set()
    print(f"모든 seed 공통 실패 rollout: {sorted(common)}  (합집합 {sorted(union)})")
    print(f"→ 공통 {len(common)} / 합집합 {len(union)}: 공통 비율 낮을수록 배치 의존(모방격차)")
    return cats, fail_by_seed, common, union


def _selfcheck():
    # classify 논리 최소 검증
    thr = 2.95
    assert classify({"success": True, "pcb": {"x": 0.15}, "max_disp_mm": 0.0,
                     "pinch_steps": 5}, thr) == "SUCCESS"
    assert classify({"success": False, "pcb": {"x": 0.15}, "max_disp_mm": 1.0,
                     "pinch_steps": 0}, thr) == "UNREACH"
    assert classify({"success": False, "pcb": {"x": 0.25}, "max_disp_mm": 6.0,
                     "pinch_steps": 0}, thr) == "NONPINCH"
    assert classify({"success": False, "pcb": {"x": 0.25}, "max_disp_mm": 1.0,
                     "pinch_steps": 0}, thr) == "SHORT"
    print("[selfcheck] classify OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dr", action="store_true", help="DR-trained(9/26) 비교 arm 분석")
    ap.add_argument("--both", action="store_true", help="nominal + DR 둘 다")
    args = ap.parse_args()
    _selfcheck()
    if args.both:
        analyze(NOMINAL_PREFIX, "nominal 배포모델 act_rs232_sim (9/18)")
        analyze(DR_PREFIX, "DR-trained 비교arm act_rs232_dr_sim (9/26)")
    elif args.dr:
        analyze(DR_PREFIX, "DR-trained 비교arm act_rs232_dr_sim (9/26)")
    else:
        analyze(NOMINAL_PREFIX, "nominal 배포모델 act_rs232_sim (9/18)")
