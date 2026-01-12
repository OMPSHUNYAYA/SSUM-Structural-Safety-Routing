import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path

EPS = 1e-12

def clamp(x, lo=-0.999999, hi=0.999999):
    return lo if x < lo else hi if x > hi else x

def atanh_safe(x):
    return math.atanh(clamp(x))

@dataclass
class RouteSpec:
    name: str
    n: int
    pattern: str

def smoothstep01(t):
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    return t * t * (3.0 - 2.0 * t)

def _guaranteed_low(a_min_for_event: float, preferred: float = -0.35) -> float:
    # Always ensure the blackout low is strictly below the deny threshold,
    # even if a_min_for_event is configured unusually.
    return min(preferred, float(a_min_for_event) - 0.05)

def make_trace(spec: RouteSpec, a_min_for_event: float):
    headers = [
        "k", "x", "x_next", "r", "dx_raw", "dx", "dx_perm",
        "a", "s", "u", "v", "R", "Psi", "event"
    ]

    rows = []
    u_prev = 0.0
    v_prev = 0.0
    m_prev = 0.0

    n = max(2, int(spec.n))
    denom = max(1, n - 1)

    # Central band and ramp sizes (deterministic, no randomness)
    band_lo = n // 3
    band_hi = (2 * n) // 3
    ramp = max(2, n // 20)

    a_low = _guaranteed_low(a_min_for_event, preferred=-0.35)

    for k in range(n):
        m = float(k)

        base_a = 0.62 + 0.06 * math.cos(2.0 * math.pi * k / denom)
        base_s = 0.16 + 0.05 * math.sin(2.0 * math.pi * k / denom)

        if spec.pattern == "free_return_corridor":
            a = base_a + 0.03 * math.cos(4.0 * math.pi * k / denom)
            s = base_s

        elif spec.pattern == "comms_blackout_band":
            a = base_a
            s = base_s
            if band_lo <= k <= band_hi:
                a = a_low

        elif spec.pattern == "comms_blackout_smooth":
            a = base_a
            s = base_s

            if k < band_lo - ramp or k > band_hi + ramp:
                pass
            elif band_lo <= k <= band_hi:
                a = a_low
            elif band_lo - ramp <= k < band_lo:
                t = (k - (band_lo - ramp)) / max(1.0, float(ramp))
                w = smoothstep01(t)
                a = (1.0 - w) * base_a + w * a_low
            elif band_hi < k <= band_hi + ramp:
                t = (k - band_hi) / max(1.0, float(ramp))
                w = smoothstep01(t)
                a = (1.0 - w) * a_low + w * base_a

        elif spec.pattern == "radiation_spike_hazard":
            a = 0.56 + 0.05 * math.cos(2.0 * math.pi * k / denom)
            s = base_s
            for kk in (n // 5, 2 * n // 5, 3 * n // 5):
                if k == kk:
                    s = 0.80

        elif spec.pattern == "midcourse_shock_denied":
            a = 0.60 + 0.04 * math.cos(2.0 * math.pi * k / denom)
            s = 0.15 + 0.04 * math.sin(2.0 * math.pi * k / denom)
            if k == n // 2:
                s = 0.98

        elif spec.pattern == "margin_erosion_denied_only":
            erosion = 0.75 * (k / denom)
            a = 0.60 - erosion + 0.03 * math.cos(2.0 * math.pi * k / denom)
            s = 0.16 + 0.02 * math.sin(2.0 * math.pi * k / denom)

        else:
            raise ValueError(f"Unknown pattern: {spec.pattern}")

        a = clamp(a)
        s = clamp(s)

        u = atanh_safe(a)
        v = atanh_safe(s)

        R = math.sqrt(u * u + v * v)
        Psi = R * R

        dx_raw = (m - m_prev)
        dx = dx_raw
        dx_perm = dx_raw

        # Event precedence: DENY must not be overwritten by SPIKE.
        # (SPIKE is meaningful only if permission is not already denied.)
        if a < float(a_min_for_event):
            event = "DENY"
        elif abs(v - v_prev) > 1.0:
            event = "SPIKE"
        else:
            event = "ROAM"

        x = float(k)
        x_next = float(k + 1)
        r = 0.0

        rows.append([
            k, x, x_next, r, dx_raw, dx, dx_perm,
            a, s, u, v, R, Psi, event
        ])

        u_prev, v_prev, m_prev = u, v, m

    return headers, rows

def write_csv(path: Path, headers, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=80)
    ap.add_argument("--out_dir", default="traces_mission")
    ap.add_argument("--include_smooth_blackout", action="store_true")
    ap.add_argument("--a_min_for_event", type=float, default=0.05)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    specs = [
        RouteSpec("routeA_free_return_corridor.csv", args.n, "free_return_corridor"),
        RouteSpec("routeB_comms_blackout_band.csv", args.n, "comms_blackout_band"),
        RouteSpec("routeC_radiation_spike_hazard.csv", args.n, "radiation_spike_hazard"),
        RouteSpec("routeD_midcourse_shock_denied.csv", args.n, "midcourse_shock_denied"),
        RouteSpec("routeE_margin_erosion_denied_only.csv", args.n, "margin_erosion_denied_only"),
    ]

    if args.include_smooth_blackout:
        specs.append(RouteSpec("routeB2_comms_blackout_smooth.csv", args.n, "comms_blackout_smooth"))

    for s in specs:
        headers, rows = make_trace(s, a_min_for_event=float(args.a_min_for_event))
        write_csv(out_dir / s.name, headers, rows)
        print("WROTE", s.name)

if __name__ == "__main__":
    main()
