# Working Note: Theorem B(ii) — Per-Resource Lagrangian Slack Under State-Dependent Coupling

Date: 2026-07-16. Status: proof-strategy note. Companion to
`freightbidbench_v04_methods_paper.md` §6.

## Goal

Prove: there exist instance families of the relocating-resource model in
which the per-resource Lagrangian slack `[min_λ L(λ) − V*] / K` is
bounded away from zero as `K → ∞` (proportional scaling), and — the
refinement the empirics motivate — grows with contention density. This
contrasts with the O(1) *total*-gap guarantees for weakly coupled DPs
whose linking constraints are state-independent and few (Brown–Zhang
2023 conditions).

## Constructions that COLLAPSE (and why that is informative)

Documented so we do not rediscover them, and because each collapse
identifies an ingredient the true construction must contain.

1. **Identical loads, single-service resources.** K resources at market
   A, N = 2K identical loads of reward r; serving relocates (one service
   per resource). At λ = 0 every per-resource optimizer takes *some*
   load, duplication is rampant — but values are identical, so
   `L(0) = K·r = V*`. **Zero gap.** Lesson: duplication does not create
   slack when the duplicated options are value-interchangeable;
   heterogeneity is necessary.

2. **Heterogeneous rewards, one-shot assignment.** Distinct rewards, one
   service each, no time structure: this is a pure assignment/knapsack
   relaxation; the assignment LP is integral and load-indexed duals
   support the optimum. **Zero (or vanishing) gap.** Lesson: without
   sequencing/chaining, per-load prices are expressive enough.

3. **Symmetric two-period chaining.** Markets A→B; scarce second-leg
   loads (m = K/2, reward R) vs abundant stay-home loads (reward r).
   Identical trucks make the indifference dual
   `λ_B = δ + R − r` exact: `L(λ*) = V*`. **Zero gap.** Lesson: with
   exchangeable resources, a single price per load equalizes paths and
   the dual closes; resource-state heterogeneity (clocks, positions) is
   necessary.

**Synthesis.** Positive slack requires *jointly*: (i) chaining (a
resource's eligibility for later loads depends on which earlier load it
took — the controlled relocation), (ii) heterogeneous per-(resource,
load) values or eligibilities induced by resource state, and (iii)
load-indexed prices that must compromise across resource states. This
matches the empirical slack signature at x2: relaxed trucks cherry-pick
chains through *unpriced* loads; duals price aggregate overuse per load,
not the state-dependent chain externalities.

## The low-risk route: verified kernel + replication

**Step 1 (kernel).** Exhibit a *small, finite* instance `I0` (target: 2
markets, 2–3 resources with heterogeneous clock states, 3–5 loads over
two periods with windows forcing state-dependent eligibility) with a
strictly positive duality gap `g0 = min_λ L(λ; I0) − V*(I0) > 0`.
Verification is *computational and exact*: `V*` by enumeration of the
joint tree; `min_λ L` by solving the finite dual (piecewise-linear
convex in ≤ 5 variables — solvable exactly by enumeration of the
per-resource best-response cells or a fine grid with a Lipschitz
certificate). The kernel search can be automated: scan small instances
drawn from the benchmark's own primitives until `g0 > 0` is certified.
The empirical x1/x2 gaps strongly suggest such kernels are common.

**Step 2 (replication).** Take `n` disjoint copies of `I0` (disjoint
markets, loads, resources). The joint problem separates:
`V* = n·V*(I0)`; the dual separates likewise (each copy's loads have
their own multipliers), so `min_λ L = n·min L(I0)` and the total gap is
`n·g0` with `K = n·k0` resources — **per-resource slack `g0/k0 > 0` for
all K.** Theorem B(ii) in its "bounded away from zero" form follows.

**Honesty check on the contrast.** Brown–Zhang's O(1) bounds live in the
regime of a *fixed number* of linking constraints as subproblems grow.
Our model has one linking constraint *per load*, and loads grow with K —
a different scaling regime, so the replication result does not
*contradict* their theorem; it shows their regime's conclusion fails in
the natural scaling for online freight (constraints ∝ K). State this
precisely in the paper — the claim is "the classical intuition does not
transfer," not "the classical theorem is wrong."

**Step 3 (density refinement — the stretch).** Replication gives
constant per-resource slack; the empirics show slack *increasing* in
density (35.6% → 37.0% → 52.2%). Candidate mechanism: the number of
*distinct feasible chains per resource* grows superlinearly with load
density while duals grow only linearly (one per load), so the pricing
deficit widens. Target statement: in a parametric kernel family
`I0(ρ)` with arrival density ρ, `g0(ρ)/V*(ρ)` is increasing in ρ over a
regime. Attack by explicit computation on the kernel family (exact,
small) + replication; a closed-form monotonicity proof on a stylized
two-period family is plausible. If only computational monotonicity is
obtained, report it as a certified numerical result on the kernel
family — still a theorem-adjacent, fully reproducible artifact.

## RESULTS (2026-07-17): kernels found — B(ii) existence secured

`scripts/find_gap_kernel.py` implements the search with exact
certificates: `V*` by joint enumeration, `min_λ L` = chain-packing LP
value (Dantzig–Wolfe) by an exact Fraction-arithmetic simplex. Across
12,000 random small instances (4 seeds): **4 certified positive-gap
kernels, relative gaps 1.2%–8.5% of V*** (`reports/gap_kernel_search*.md`).
The best kernel (V* = 41, LP = 89/2): 3 trucks with staggered
availabilities and budget 2, 6 loads in cyclic geography — a
half-integral LP optimum, i.e. the odd-cycle conflict structure realized
through time + geography + budgets, precisely the three ingredients the
collapse analysis predicted. With the replication lemma, **B(ii)'s
bounded-away-from-zero form is now essentially proven** (write-up
pending).

**Second finding — kernel rarity (~0.03%) is itself scientific.** At
small scale the Lagrangian is almost always tight; duality gaps are rare
and small. Two consequences: (i) the benchmark's large bound−policy gaps
(36–52%) cannot be assumed to be mostly duality gap at small scale —
the split at benchmark scale remains open, and the density-growth
refinement (Step 3) is where the interesting theory now lives; (ii) the
paper should report the rarity honestly — it sharpens, not weakens, the
claim ("gaps exist and replicate; they are structurally tied to cyclic
heterogeneous chaining, and grow with density" — the last clause pending
Step 3).

## Theorem B(i) proof architecture (fluid-limit policy consistency)

**Honesty first.** The empirical corridor for V*/K at x2 is wide
([policy/K, bound/K] = [15.1k, 31.6k]); "V^π/V* → 1" in the
critical/supercritical regime is NOT currently supported by evidence and
may be false. The provable target splits by regime:

- **Subcritical regime** (fluid contention vanishes: service capacity
  strictly exceeds dual-priced demand): target `V^{π_λ}/V* → 1`.
  Lemma chain:
  (L1) fluid relaxation of the aggregated recursion; its LP and prices.
  (L2) price consistency: λ̂ fitted on one sample path converges to
       fluid prices (LLN over arrival blocks; the portability empirics
       are the finite-sample shadow).
  (L3) exchange/coupling: the same-time spatial gradient policy tracks
       the fluid assignment except on an O(√K) contention set (Lemma A3
       supplies the exchange step).
  (L4) regeneration: HOS clocks couple epochs; break via renewal at
       rest events (each resource's (market, clock) process regenerates
       on rests; subcriticality keeps regeneration cycles uniformly
       integrable). **Main technical risk lives here.**
  (L5) concentration: realized contention → fluid contention
       (Azuma/Bernstein over load blocks).
- **Critical regime** (tight/scarce economics): weaken to
  `V^{π_λ} ≥ (1 − ε(ρ)) · V_fluid` with explicit density-dependent
  `ε`, or a comparative statement (π_λ asymptotically dominates every
  price-taking policy). State the →1 question as open, supported by the
  kernel-rarity finding at small scale and left open at high density.

**Sequencing:** prove subcritical B(i) end-to-end first (cleanest
positive result); attempt L4 under a bounded-cycle assumption before
the general renewal argument; document the critical-regime obstruction
precisely (degenerate fluid duals at ρ = 1).

Risk state after this note: **B(ii) LOW (existence done, write-up
pending; density refinement MEDIUM). B(i) subcritical MEDIUM; critical
OPEN.**
