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
        raise SystemExit(f"FAIL: {label}: got={got} expected={exp}")


def must_contains(label, text, needle):
    if needle not in (text or ""):
        raise SystemExit(f"FAIL: {label}: missing '{needle}' in '{text}'")


def must_not_contains(label, text, needle):
    if needle in (text or ""):
        raise SystemExit(f"FAIL: {label}: must not contain '{needle}' in '{text}'")


def main():
    summary_csv = "ssr_mission_summary.csv"
    if len(sys.argv) >= 2:
        summary_csv = sys.argv[1]

    rows = read_summary(summary_csv)

    A = must_find(rows, "routeA_free_return_corridor.csv")
    B = must_find(rows, "routeB_comms_blackout_band.csv")
    B2 = must_find(rows, "routeB2_comms_blackout_smooth.csv")
    C = must_find(rows, "routeC_radiation_spike_hazard.csv")
    D = must_find(rows, "routeD_midcourse_shock_denied.csv")
    E = must_find(rows, "routeE_margin_erosion_denied_only.csv")

    # Allowed
    must_equal("A denied", A.get("denied"), "0")
    must_equal("C denied", C.get("denied"), "0")

    # Permission denied
    must_equal("B denied", B.get("denied"), "1")
    must_contains("B deny_reason", B.get("deny_reason", ""), "a<a_min")
    must_not_contains("B deny_reason", B.get("deny_reason", ""), "step>thr")

    must_equal("B2 denied", B2.get("denied"), "1")
    must_contains("B2 deny_reason", B2.get("deny_reason", ""), "a<a_min")
    must_not_contains("B2 deny_reason", B2.get("deny_reason", ""), "step>thr")

    must_equal("E denied", E.get("denied"), "1")
    must_contains("E deny_reason", E.get("deny_reason", ""), "a<a_min")
    must_not_contains("E deny_reason", E.get("deny_reason", ""), "step>thr")

    # Spike denied (requires spike mode enabled in SSR command)
    must_equal("D denied", D.get("denied"), "1")
    must_contains("D deny_reason", D.get("deny_reason", ""), "step>thr")
    must_not_contains("D deny_reason", D.get("deny_reason", ""), "a<a_min")

    print("SSR MISSION TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
