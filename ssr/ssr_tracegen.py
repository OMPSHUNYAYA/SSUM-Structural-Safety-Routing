import csv
import math
from dataclasses import dataclass

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


def make_trace(spec: RouteSpec):
    rows = []
    m_prev = 0.0
    u_prev = 0.0
    v_prev = 0.0

    headers = [
        "k", "x", "x_next", "r", "dx_raw", "dx", "dx_perm",
        "a", "s", "u", "v", "R", "Psi", "event"
    ]

    for k in range(spec.n):
        m = float(k)

        if spec.pattern == "corridor":
            a = 0.65 + 0.10 * math.cos(2 * math.pi * k / max(1, spec.n - 1))
            s = 0.15 + 0.05 * math.sin(2 * math.pi * k / max(1, spec.n - 1))

        elif spec.pattern == "permission_collapse":
            a_base = 0.55 + 0.05 * math.cos(2 * math.pi * k / max(1, spec.n - 1))
            s = 0.20 + 0.05 * math.sin(2 * math.pi * k / max(1, spec.n - 1))

            k1 = spec.n // 3
            k2 = (2 * spec.n) // 3

            if k1 <= k <= k2:
                t = (k - k1) / max(1, (k2 - k1))
                w = 0.5 - 0.5 * math.cos(2 * math.pi * t)   # smooth 0->1->0
                a = a_base - (0.90 * w)                     # min approx -0.35
            else:
                a = a_base

        elif spec.pattern == "spike_hazard":
            a = 0.55 + 0.06 * math.cos(2 * math.pi * k / max(1, spec.n - 1))
            s = 0.18 + 0.06 * math.sin(2 * math.pi * k / max(1, spec.n - 1))
            if k in {spec.n // 4, spec.n // 2, (3 * spec.n) // 4}:
                s = 0.85

        elif spec.pattern == "spike_denied":
            a = 0.60 + 0.04 * math.cos(2 * math.pi * k / max(1, spec.n - 1))
            s = 0.15 + 0.04 * math.sin(2 * math.pi * k / max(1, spec.n - 1))
            if k == spec.n // 2:
                s = 0.98

        elif spec.pattern == "permission_denied_only":
            a_base = 0.60 + 0.02 * math.cos(2 * math.pi * k / max(1, spec.n - 1))
            k1 = spec.n // 3
            k2 = (2 * spec.n) // 3

            if k1 <= k <= k2:
                t = (k - k1) / max(1, (k2 - k1))
                w = 0.5 - 0.5 * math.cos(2 * math.pi * t)
                a = a_base - (1.00 * w)
            else:
                a = a_base

            s = 0.12

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

        event = "ROAM"
        if a < 0:
            event = "DENY"
        if abs(v - v_prev) > 1.0:
            event = "SPIKE"

        x = float(k)
        x_next = float(k + 1)
        r = 0.0

        rows.append([
            k, x, x_next, r, dx_raw, dx, dx_perm,
            a, s, u, v, R, Psi, event
        ])

        u_prev, v_prev, m_prev = u, v, m

    return headers, rows


def write_csv(path, headers, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)


def main():
    specs = [
        RouteSpec("routeA_corridor.csv", 60, "corridor"),
        RouteSpec("routeB_permission_collapse.csv", 60, "permission_collapse"),
        RouteSpec("routeC_spike_hazard.csv", 60, "spike_hazard"),
        RouteSpec("routeD_spike_denied.csv", 60, "spike_denied"),
        RouteSpec("routeE_permission_denied_only.csv", 60, "permission_denied_only"),
    ]

    for s in specs:
        headers, rows = make_trace(s)
        write_csv(s.name, headers, rows)
        print("WROTE", s.name)


if __name__ == "__main__":
    main()
