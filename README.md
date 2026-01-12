# ⭐ **Shunyaya Structural Universal Mathematics — Structural Safety Routing (SSUM-SSR)**

**Deny Unsafe Routes by Structure First — Then Rank What Remains**

![STARS](https://img.shields.io/badge/STARS-green) ![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-green)

**Deterministic • Structural Safety Routing • Route Admissibility • Collapse Gates • Reproducible Ranking • Observation-Only**

---

## 🔎 **What Is Structural Safety Routing?**

Structural Safety Routing (SSUM-SSR) is a deterministic system that decides **which routes are admissible before any optimization or selection occurs**.

Classical routing typically asks:
- Which route is shortest?
- Which route is fastest?
- Which route has the best score?

**SSUM-SSR asks a prior question:**

> **Which routes are structurally safe enough to be considered at all?**

SSUM-SSR is **not** a routing optimizer.  
It does **not** compute routes, alter solvers, or impose heuristics.

It evaluates route traces and produces:
- **ALLOW / DENY** decisions with explicit reasons
- safety-focused summaries (permission collapse, spike hazards)
- reproducible ranking **among allowed routes only**

There are:
- no probabilistic assumptions
- no training
- no heuristics
- no hidden state

Everything is **deterministic and audit-friendly**.

This framework demonstrates **domain independence** through two built-in trace sets:
- **Canonical routes (A–E)** for clean public validation
- **Mission-style routes (A–E plus optional B2)** using the same engine without modification

---

## 🔗 **Quick Links**

### **Docs**
- [Concept Flyer (PDF)](docs/Concept-Flyer_SSUM-SSR_v1.4.pdf)
- [Full Specification (PDF)](docs/SSUM-SSR_v1.4.pdf)
- [Quickstart Guide](docs/Quickstart.md)
- [FAQ](docs/FAQ.md)

### **Structural Safety Routing (SSR)**
- [`ssr_structural_safety_routing.py`](ssr/ssr_structural_safety_routing.py) — core SSR engine (allow/deny, gates, ranking)
- [`ssr_tracegen.py`](ssr/ssr_tracegen.py) — deterministic canonical route generator
- [`ssr_tests.py`](ssr/ssr_tests.py) — determinism and correctness verification
- [`traces/`](ssr/traces/) — canonical route traces (A–E)

### **Mission Space Extension**
- [`ssr_tracegen_mission.py`](mission_space/ssr_tracegen_mission.py) — mission-style trace generator
- [`ssr_tests_mission.py`](mission_space/ssr_tests_mission.py) — mission determinism verification
- [`traces/`](mission_space/traces/) — mission-space route traces (A–E, optional B2)

---

## 🗺️ **Route Classes and Structural Failure Modes (Quick Reference)**

SSUM-SSR evaluates routes by **structural admissibility first**, then ranks only what remains permissible.

| Route | Interpretation                     | Structural Outcome        |
|------:|-----------------------------------|---------------------------|
| A     | Structurally neutral corridor     | Allowed                   |
| B     | Abrupt permission collapse        | Denied (Permission)       |
| B2    | Gradual permission erosion        | Denied (Permission)       |
| C     | Hazardous region with stability   | Allowed                   |
| D     | Localized structural shock        | Denied (Spike)            |
| E     | Margin erosion below threshold    | Denied (Permission)       |

**Notes**
- Routes B and B2 demonstrate permission-based denial, not spike hazards.
- Route B2 isolates gradual permission loss versus B’s abrupt band.
- Routes A–E appear in both canonical and mission-style traces.
- Mission-style traces reuse the **exact same SSR engine with zero modifications**.

**Admissibility is binary and final.**  
Denied routes are **never ranked**.

---

## 🎯 **Problem Statement — Why Classical Routing Misses Safety**

Classical routing treats all candidates as comparable.

But many real systems violate that assumption:
- a route can be numerically short but structurally unsafe
- a route can “complete” while accumulating collapse pressure
- a route can remain permissible yet suffer rare shock events

Ranking unsafe routes produces **false confidence**.

SSUM-SSR introduces a deterministic safety layer:

> **deny first — then rank**

---

## 🧱 **Structural State and Collapse Rule**

SSR operates on structural triples:

`(m_k, a_k, s_k)`

- `m_k` = classical progress / meaning coordinate  
- `a_k` = alignment (structural permission)  
- `s_k` = stress (structural resistance with memory)

**Collapse rule (invariant):**

`phi((m,a,s)) = m`

This guarantees:
- classical meaning is never overwritten
- structural channels observe safety without changing truth
- SSR always collapses back to classical interpretation

---

## 📐 **Structural Channels and Structural Distance**

SSR uses hyperbolic structural channels:

- `u_k = atanh(clamp(a_k))`
- `v_k = atanh(clamp(s_k))`

**Why hyperbolic channels?**
- `a_k` and `s_k` are bounded in `(-1, 1)`
- `atanh` maps bounded values to unbounded structural space
- proximity to limits expands rapidly
- boundary pressure becomes visible before failure

No heuristics.  
No saturation.

**Structural Distance (per step):**

`D_k = sqrt((m_k - m_{k-1})^2 + (u_k - u_{k-1})^2 + (v_k - v_{k-1})^2)`

**Cumulative structural distance:**

`L_struct = sum_k D_k`

**Classical distance:**

`L_classical = sum_k |m_k - m_{k-1}|`

**Structural efficiency (diagnostic):**

`eta = L_struct / L_classical`

**Structural Invariance Property**

For every step:

`D_k >= |m_k - m_{k-1}|`

Therefore:

`L_struct >= L_classical`

with equality **iff** `u_k` and `v_k` remain constant.

Structural Distance is a **strictly conservative extension** of classical distance.

---

## 🚦 **SSR Gates (Allow / Deny)**

### **Permission Gate**
Deny if:
- `a_k < a_min`

Permission collapse is not “worse” — it is **inadmissible**.  
Once denied, a route cannot recover.

### **Spike (Shock) Gate**

**Relative spike mode (recommended):**
- compute `p95_step` from `D_k`
- define `thr = step_spike_k * p95_step`
- deny if any `D_k > thr`

**Absolute spike mode (mission validation):**
- deny if any `D_k > step_spike`

This detects unsafe structural violence deterministically.

### **Deny Mode**
`deny_mode=any` means:
- **any single violation denies the route**

Safety-conservative by design.

---

## 📊 **Example Output (Canonical Routes)**

**ALLOWED**
- `routeA_corridor.csv`
- `routeC_spike_hazard.csv`

**DENIED**
- `routeB_permission_collapse.csv` (permission)
- `routeD_spike_denied.csv` (spike)
- `routeE_permission_denied_only.csv` (permission)

Admissibility is enforced **before** optimality.

---

## 📊 **Example Output (Mission-Style Routes)**

Mission traces reuse the same SSR engine.

Typical outcomes:
- Free-return corridor → allowed
- Comms blackout → denied by permission
- Radiation hazard → allowed but higher structural cost
- Midcourse shock → denied by spike
- Margin erosion → denied by permission

Mission traces are **structural demonstrations only**, not physics models or mission planners.

---

## 🧪 **What SSUM-SSR Demonstrates**

SSUM-SSR deterministically separates:
- admissibility
- severity
- ranking

Canonical and mission traces prove:
- failure modes are isolated
- no tuning is required
- logic generalizes across domains

No ambiguity.  
No heuristics.  
No learning.

---

## ▶️ **Running SSUM-SSR (Python)**

Generate canonical routes:
- `python ssr_tracegen.py`

Evaluate:
- `python ssr_structural_safety_routing.py --in ...`

Verify determinism:
- `python ssr_tests.py`

Expected:
- `SSR TESTS PASSED`

Mission determinism verification:
- `python ssr_tests_mission.py ssr_mission_summary.csv`

---

## ❄️ **Determinism & Freeze Contract**

Identical inputs guarantee:
- identical allow/deny decisions
- identical reasons
- identical rankings

No randomness.  
No machine dependence.  
No hidden state.

---

## 🚫 **What Structural Safety Routing Is Not**

SSUM-SSR is **not**:
- a routing solver
- an optimizer
- a controller
- a probabilistic model
- a learning system
- a safety certification tool

It denies unsafe routes by structure and explains why.

---

## 🔍 **Interpretation Boundaries**

SSUM-SSR is **observation-only**.
- `a` and `s` are structural observables
- permission describes admissibility in SSUM space
- no real-world safety guarantees

Not for autonomous or safety-critical use.

---

## 📄 **License & Attribution**

**CC BY 4.0 — Public Research Release**

Attribution:
**Shunyaya Structural Universal Mathematics — Structural Safety Routing (SSUM-SSR)**

Built within:
**Shunyaya Structural Universal Mathematics (SSUM)**

No warranty. Provided “as is”.

---

## 🔗 Related Work (Optional)

- **SSUM-Structural-Distance**  
  Deterministic measurement of structural cost and efficiency across trajectories.  
  https://github.com/OMPSHUNYAYA/SSUM-Structural-Distance

---

## 🏷️ **Topics**

SSUM-SSR, Structural-Safety-Routing, Structural-Mathematics, Deterministic-Mathematics, Route-Admissibility, Structural-Distance, Collapse-Gates, Explainable-Routing, Shunyaya
