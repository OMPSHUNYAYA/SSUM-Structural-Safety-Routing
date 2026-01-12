# ⭐ **Shunyaya Structural Universal Mathematics — Structural Safety Routing (SSUM-SSR)**

## **Quickstart**

**Deterministic • Structural Safety Routing • Route Admissibility • Collapse Gates • Reproducible Ranking**

---

## **WHAT YOU NEED**

Structural Safety Routing is intentionally **minimal**, **deterministic**, and **implementation-neutral**.

### **Requirements**
- Python 3.9+
- Standard library only (no external dependencies)

Everything is:
- deterministic
- offline
- reproducible
- identical across machines

No randomness.  
No training.  
No probabilistic heuristics.  
No adaptive tuning.

---

## **MINIMAL PROJECT LAYOUT**

A minimal SSUM-SSR release contains:

```
ssr/  
ssr_structural_safety_routing.py  
ssr_tracegen.py  
ssr_tests.py  
traces/  
routeA_corridor.csv  
routeB_permission_collapse.csv  
routeC_spike_hazard.csv  
routeD_spike_denied.csv  
routeE_permission_denied_only.csv  
```

```
mission_space/  
ssr_structural_safety_routing.py  
ssr_tracegen_mission.py  
ssr_tests_mission.py  
traces/  
routeA_free_return_corridor.csv  
routeB_comms_blackout_band.csv  
routeB2_comms_blackout_smooth.csv  
routeC_radiation_spike_hazard.csv  
routeD_midcourse_shock_denied.csv  
routeE_margin_erosion_denied_only.csv  
```

**Notes**
- Canonical traces demonstrate SSR behavior in a domain-neutral setting.
- Mission-space traces reinterpret the same structure for space-style scenarios.
- **Both reuse the exact same frozen SSR engine.**
- No build step. No compilation. No external libraries.

---

## **ONE-MINUTE MENTAL MODEL**

Classical routing asks:  
“How short / fast / cheap is the path?”

Structural Safety Routing asks first:  
“Is this route admissible to traverse at all?”

SSR does **not** optimize routes.  
SSR **filters routes by structural safety**, then ranks only those that remain admissible.

---

## **CORE STRUCTURAL IDEA (IN ONE LINE)**

A route is valid only where structure permits.  
All other motion accumulates collapse pressure until denial.

---

## **WHAT SSR TRACKS**

SSR evaluates routes using deterministic structural observables:
- alignment `a_k` (permission)
- stress `s_k` (resistance with memory)

Mapped into bounded structural channels:
- `u_k = atanh(clamp(a_k))`
- `v_k = atanh(clamp(s_k))`

Structural posture quantities:
- `R_k = sqrt(u_k^2 + v_k^2)`
- `Psi_k = R_k^2`

SSR evaluates stepwise structural motion using Structural Distance:
- `D_k = sqrt((m_k - m_{k-1})^2 + (u_k - u_{k-1})^2 + (v_k - v_{k-1})^2)`

Cumulative structural distance:
- `L_struct = sum_k D_k`

---

## **SSR SAFETY GATES**

### **Gate 1 — Permission Gate**

A route is denied if permission falls below a minimum threshold.

Deny if any step violates:
- `a_k < a_min`

This is categorical.  
Once denied, a route cannot recover.

---

### **Gate 2 — Spike Gate (Structural Shock)**

A route is denied if structural step distance becomes unsafe.

**Absolute spike gate**  
Deny if any step violates:
- `D_k > step_spike`

**Relative spike gate (recommended)**  
Define threshold:
- `thr = step_spike_k * p95_step`

Deny if any step violates:
- `D_k > thr`

This captures structural violence even when permission remains valid.

---

## **SSR OUTPUTS (WHAT YOU GET)**

SSR produces a deterministic route report with:
- Allowed vs Denied classification
- Denial reasons (permission and/or spikes)
- Structural Distance: `L_struct`
- Structural Efficiency: `eta = L_struct / L_classical`
- Step statistics: `p95_step`, `max_step`
- Maximum structural magnitude: `max_R`

Only **allowed routes** are ranked.  
Denied routes are reported but **never compared**.

---

## **QUICK RUN — CANONICAL ROUTES**

Generate deterministic canonical traces:
- `python ssr_tracegen.py`

Evaluate and rank (safety-first):
- `python ssr_structural_safety_routing.py --in routeA_corridor.csv routeB_permission_collapse.csv routeC_spike_hazard.csv routeD_spike_denied.csv routeE_permission_denied_only.csv --a_min 0.05 --step_spike_mode rel_p95 --step_spike_k 1.2 --deny_mode any --rank max_step --out ssr_routing_summary_synthetic.csv`

**Expected behavior**
- Route A → allowed and safest
- Route C → allowed but riskier
- Routes B and E → denied by permission
- Route D → denied by spike

---

## **OPTIONAL — MISSION SPACE EXAMPLES**

Mission-space examples reuse the **same SSR engine with zero modifications**.  
Only the interpretation of structural observables changes.

Generate mission-style traces:
- `python ssr_tracegen_mission.py`

Optional smooth permission blackout:
- `python ssr_tracegen_mission.py --include_smooth_blackout`

Evaluate mission traces:
- `python ssr_structural_safety_routing.py --in routeA_free_return_corridor.csv routeB_comms_blackout_band.csv routeB2_comms_blackout_smooth.csv routeC_radiation_spike_hazard.csv routeD_midcourse_shock_denied.csv routeE_margin_erosion_denied_only.csv --a_min 0.05 --step_spike_mode abs --step_spike 1.8 --deny_mode any --rank L_struct --out ssr_mission_summary.csv`

Determinism verification:
- `python ssr_tests_mission.py ssr_mission_summary.csv`

Mission examples demonstrate:
- safe corridors
- permission blackout denial
- admissible radiation exposure
- spike-only shock denial
- gradual margin erosion denial

These are **structural demonstrations only** — not physics models, simulations, or mission planners.

---

## **DETERMINISM GUARANTEE**

Given identical inputs:
- identical allow/deny classification
- identical denial reasons
- identical rankings
- identical outputs

No randomness.  
No machine dependence.  
No hidden state.

---

## **WHAT SSR IS — AND IS NOT**

SSUM-SSR **is**:
- a structural admissibility filter
- a deterministic safety gate for routes
- an observation-only safety layer

SSUM-SSR **is not**:
- a routing algorithm
- an optimizer
- a controller
- a predictive risk model
- a decision system

It does not make decisions.  
It makes **structural safety observable**.

---

## **ONE-LINE SUMMARY**

Structural Safety Routing lets you deterministically classify and rank routes by structural admissibility — across domains — using permission and shock gates, without training, probability, or hidden state.
