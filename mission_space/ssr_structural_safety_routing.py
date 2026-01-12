import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

EPS = 1e-12


def to_float(x, default=None):
    try:
        return float(x)
    except Exception:
        return default


def clamp(x: float, lo: float, hi: float) -> float:
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def atanh_safe(x: float, eps: float = 1e-12) -> float:
    x = float(x)
    x = clamp(x, -1.0 + eps, 1.0 - eps)
    return 0.5 * math.log((1.0 + x) / (1.0 - x))


def percentile(sorted_vals: List[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    if p <= 0:
        return sorted_vals[0]
    if p >= 100:
        return sorted_vals[-1]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    d0 = sorted_vals[f] * (c - k)
    d1 = sorted_vals[c] * (k - f)
    return d0 + d1


@dataclass
class RouteMetrics:
    route: str
    rows: int

    L_classical: float
    L_struct: float
    eta: float

    denied: int
    deny_reason: str

    a_min_seen: float
    deny_count_a: int

    median_step: float
    p95_step: float
    max_step: float

    max_R: float
    max_Psi: float


def read_rows(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        rows = list(rdr)
        if not rows:
            raise SystemExit(f"Empty CSV: {path.as_posix()}")
        cols = rdr.fieldnames or []
    return rows, cols


def compute_base(path: Path, eps_atanh: float) -> Tuple[RouteMetrics, List[float], List[float]]:
    rows, cols = read_rows(path)

    has_u = "u" in cols
    has_v = "v" in cols
    has_a = "a" in cols
    has_s = "s" in cols

    if "dx" not in cols:
        raise SystemExit(f"Missing required column 'dx' in {path.name}")

    if not ((has_u and has_v) or (has_a and has_s)):
        raise SystemExit(
            f"{path.name}: need either ('u','v') OR ('a','s') columns, along with 'dx'."
        )

    dx: List[float] = []
    u: List[float] = []
    v: List[float] = []
    a_vals: List[float] = []

    R: List[float] = []
    Psi: List[float] = []

    for r in rows:
        dx_i = to_float(r.get("dx"), 0.0) or 0.0
        dx.append(dx_i)

        if has_u and has_v:
            u_i = to_float(r.get("u"), 0.0) or 0.0
            v_i = to_float(r.get("v"), 0.0) or 0.0
            u.append(u_i)
            v.append(v_i)
            if has_a:
                a_vals.append(to_float(r.get("a"), float("nan")))
            else:
                a_vals.append(float("nan"))
        else:
            a_i = to_float(r.get("a"), 0.0) or 0.0
            s_i = to_float(r.get("s"), 0.0) or 0.0
            a_vals.append(a_i)
            u.append(atanh_safe(a_i, eps=eps_atanh))
            v.append(atanh_safe(s_i, eps=eps_atanh))

        r_i = math.sqrt(u[-1] * u[-1] + v[-1] * v[-1])
        psi_i = 0.5 * (u[-1] * u[-1] + v[-1] * v[-1])
        R.append(r_i)
        Psi.append(psi_i)

    L_classical = sum(abs(x) for x in dx)

    step_costs: List[float] = []
    L_struct = 0.0
    for i in range(len(rows) - 1):
        du = u[i + 1] - u[i]
        dv = v[i + 1] - v[i]
        step = math.sqrt(dx[i] * dx[i] + du * du + dv * dv)
        step_costs.append(step)
        L_struct += step
    if len(rows) >= 1:
        L_struct += abs(dx[-1])

    eta = L_struct / (L_classical + EPS)

    sc_sorted = sorted(step_costs) if step_costs else [0.0]
    med_step = percentile(sc_sorted, 50.0)
    p95_step = percentile(sc_sorted, 95.0)
    max_step = sc_sorted[-1] if sc_sorted else 0.0

    a_min_seen = float("inf")
    deny_count_a = 0
    for av in a_vals:
        if av == av:
            a_min_seen = min(a_min_seen, av)

    if a_min_seen == float("inf"):
        a_min_seen = float("nan")

    rm = RouteMetrics(
        route=path.name,
        rows=len(rows),
        L_classical=L_classical,
        L_struct=L_struct,
        eta=eta,
        denied=0,
        deny_reason="",
        a_min_seen=a_min_seen,
        deny_count_a=0,
        median_step=med_step,
        p95_step=p95_step,
        max_step=max_step,
        max_R=max(R) if R else 0.0,
        max_Psi=max(Psi) if Psi else 0.0,
    )
    return rm, step_costs, a_vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inputs", nargs="+", required=True, help="One or more route trace CSVs")

    ap.add_argument("--a_min", type=float, default=0.05, help="Permission gate: deny if a < a_min (if 'a' present)")
    ap.add_argument("--eps", type=float, default=1e-12, help="atanh clamp epsilon (if computing u,v from a,s)")

    ap.add_argument("--step_spike_mode", choices=["none", "abs", "rel_p95", "rel_median"], default="none",
                    help="Spike gate mode")
    ap.add_argument("--step_spike", type=float, default=None, help="(abs mode) deny if any step > step_spike")
    ap.add_argument("--step_spike_k", type=float, default=1.2, help="(relative modes) threshold multiplier")

    ap.add_argument("--deny_mode", choices=["any", "fraction"], default="any", help="Deny on any violation, or by fraction")
    ap.add_argument("--deny_frac", type=float, default=0.01, help="(fraction mode) deny if violations/rows > deny_frac")

    ap.add_argument("--rank", choices=["L_struct", "eta", "p95_step", "max_step"], default="L_struct",
                    help="Ranking metric among allowed routes")
    ap.add_argument("--out", default="ssr_routing_summary.csv", help="Output summary CSV")

    args = ap.parse_args()

    routes: List[RouteMetrics] = []
    steps_map: Dict[str, List[float]] = {}
    a_map: Dict[str, List[float]] = {}

    for p in args.inputs:
        path = Path(p)
        if not path.exists():
            raise SystemExit(f"Not found: {p}")
        rm, step_costs, a_vals = compute_base(path=path, eps_atanh=args.eps)
        routes.append(rm)
        steps_map[rm.route] = step_costs
        a_map[rm.route] = a_vals

    for r in routes:
        a_vals = a_map[r.route]
        step_costs = steps_map[r.route]

        deny_count_a = 0
        if r.a_min_seen == r.a_min_seen:
            for av in a_vals:
                if av == av and av < args.a_min:
                    deny_count_a += 1

        thr = None
        if args.step_spike_mode == "abs":
            if args.step_spike is None:
                raise SystemExit("--step_spike required when --step_spike_mode abs")
            thr = float(args.step_spike)
        elif args.step_spike_mode == "rel_p95":
            thr = float(args.step_spike_k) * float(r.p95_step)
        elif args.step_spike_mode == "rel_median":
            thr = float(args.step_spike_k) * float(r.median_step)

        deny_count_step = 0
        if thr is not None:
            for st in step_costs:
                if st > thr:
                    deny_count_step += 1

        r.deny_count_a = deny_count_a

        denied = 0
        reasons: List[str] = []

        if args.deny_mode == "any":
            if deny_count_a > 0:
                reasons.append(f"a<a_min ({deny_count_a})")
            if thr is not None and deny_count_step > 0:
                reasons.append(f"step>thr ({deny_count_step})")
            if reasons:
                denied = 1

        else:
            if r.a_min_seen == r.a_min_seen:
                frac_a = deny_count_a / max(1, r.rows)
                if frac_a > args.deny_frac:
                    reasons.append(f"a<a_min frac={frac_a:.6g}>{args.deny_frac}")
            if thr is not None:
                frac_s = deny_count_step / max(1, max(1, len(step_costs)))
                if frac_s > args.deny_frac:
                    reasons.append(f"step>thr frac={frac_s:.6g}>{args.deny_frac}")
            if reasons:
                denied = 1

        r.denied = denied
        r.deny_reason = "; ".join(reasons)

    keymap = {
        "L_struct": lambda r: r.L_struct,
        "eta": lambda r: r.eta,
        "p95_step": lambda r: r.p95_step,
        "max_step": lambda r: r.max_step,
    }

    fields = [
        "route", "rows",
        "denied", "deny_reason",
        "L_classical", "L_struct", "eta",
        "a_min_seen", "deny_count_a",
        "median_step", "p95_step", "max_step",
        "max_R", "max_Psi",
        "spike_mode", "spike_thr"
    ]

    out_path = Path(args.out)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in routes:
            thr = ""
            if args.step_spike_mode == "abs" and args.step_spike is not None:
                thr = f"{float(args.step_spike):.15g}"
            elif args.step_spike_mode == "rel_p95":
                thr = f"{(float(args.step_spike_k) * float(r.p95_step)):.15g}"
            elif args.step_spike_mode == "rel_median":
                thr = f"{(float(args.step_spike_k) * float(r.median_step)):.15g}"

            w.writerow({
                "route": r.route,
                "rows": r.rows,
                "denied": r.denied,
                "deny_reason": r.deny_reason,
                "L_classical": f"{r.L_classical:.15g}",
                "L_struct": f"{r.L_struct:.15g}",
                "eta": f"{r.eta:.15g}",
                "a_min_seen": "" if (r.a_min_seen != r.a_min_seen) else f"{r.a_min_seen:.15g}",
                "deny_count_a": r.deny_count_a,
                "median_step": f"{r.median_step:.15g}",
                "p95_step": f"{r.p95_step:.15g}",
                "max_step": f"{r.max_step:.15g}",
                "max_R": f"{r.max_R:.15g}",
                "max_Psi": f"{r.max_Psi:.15g}",
                "spike_mode": args.step_spike_mode,
                "spike_thr": thr,
            })

    allowed = [r for r in routes if r.denied == 0]
    denied = [r for r in routes if r.denied == 1]
    allowed.sort(key=keymap[args.rank])

    print("SSUM-SSR — Structural Safety Routing (deterministic, observation-only)")
    print(f"Gate: a_min={args.a_min} | spike_mode={args.step_spike_mode} | deny_mode={args.deny_mode} | rank={args.rank}")
    if args.step_spike_mode == "abs":
        print(f"Spike abs: step_spike={args.step_spike}")
    elif args.step_spike_mode in ("rel_p95", "rel_median"):
        print(f"Spike relative: k={args.step_spike_k}")
    print("")

    if allowed:
        print("ALLOWED (ranked):")
        for i, r in enumerate(allowed, 1):
            print(
                f"{i:02d}  {r.route}  "
                f"L_struct={r.L_struct:.6g}  eta={r.eta:.6g}  "
                f"p95_step={r.p95_step:.6g}  max_step={r.max_step:.6g}  max_R={r.max_R:.6g}"
            )
    else:
        print("ALLOWED: none")

    print("")
    if denied:
        print("DENIED:")
        for r in denied:
            print(
                f"- {r.route}  reason={r.deny_reason}  "
                f"a_min_seen={'NA' if (r.a_min_seen!=r.a_min_seen) else f'{r.a_min_seen:.6g}'}  "
                f"L_struct={r.L_struct:.6g}  eta={r.eta:.6g}"
            )
    else:
        print("DENIED: none")

    print("")
    print(f"WROTE {out_path.as_posix()}")


if __name__ == "__main__":
    main()
