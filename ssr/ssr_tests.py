import csv
import sys


def read_summary(path):
    rows = []
    with open(path, "r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    if not rows:
        raise SystemExit("Empty summary CSV: " + path)
    return rows


def must_find(rows, route_name):
    for r in rows:
        if (r.get("route") or "").strip() == route_name:
            return r
    raise SystemExit("Missing route in summary: " + route_name)


def must_equal(label, got, exp):
    if str(got) != str(exp):
        raise SystemExit(f"{label} mismatch: got={got} expected={exp}")


def must_contains(label, got, needle):
    if needle not in (got or ""):
        raise SystemExit(f"{label} missing '{needle}': got={got}")


def must_not_contains(label, got, needle):
    if needle in (got or ""):
        raise SystemExit(f"{label} must NOT contain '{needle}': got={got}")


def main():
    summary_csv = "ssr_routing_summary.csv"
    if len(sys.argv) >= 2:
        summary_csv = sys.argv[1]

    rows = read_summary(summary_csv)

    A = must_find(rows, "routeA_corridor.csv")
    B = must_find(rows, "routeB_permission_collapse.csv")
    C = must_find(rows, "routeC_spike_hazard.csv")
    D = must_find(rows, "routeD_spike_denied.csv")
    E = must_find(rows, "routeE_permission_denied_only.csv")

    must_equal("A denied", A.get("denied"), "0")
    must_equal("C denied", C.get("denied"), "0")

    must_equal("B denied", B.get("denied"), "1")
    must_equal("D denied", D.get("denied"), "1")
    must_equal("E denied", E.get("denied"), "1")

    must_contains("B deny_reason", B.get("deny_reason", ""), "a<a_min")
    must_not_contains("B deny_reason", B.get("deny_reason", ""), "step>thr")

    must_contains("D deny_reason", D.get("deny_reason", ""), "step>thr")
    must_not_contains("D deny_reason", D.get("deny_reason", ""), "a<a_min")

    must_contains("E deny_reason", E.get("deny_reason", ""), "a<a_min")
    must_not_contains("E deny_reason", E.get("deny_reason", ""), "step>thr")

    print("SSR TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
