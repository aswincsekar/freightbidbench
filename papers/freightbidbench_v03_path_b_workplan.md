# FreightBidBench v0.3 — Path B Workplan: TransSci-Targeted Submission

Date: 2026-05-19. Status: planning + Phase 1 prototype lands.

## Phase 1 Prototype Result (2026-05-19)

The Theorem 1 Lagrangian-per-truck bound prototype landed and ran
end-to-end on the full `tight` scenario (70 trucks, 995 loads, eval seed
20260507). Two-stage execution: 30 cold-start iterations at step
$\sqrt{n}$-diminishing scale 100, then 20 more iterations warm-started
from the iter-30 dual prices at the same step (offset by 30 in the
schedule). Total wall-clock ~3.4 hours.

| Quantity | Value |
| --- | ---: |
| LP relaxation (reference) | $2,377,500 |
| Lagrangian L(0) (no duals) | $2,399,449 |
| Lagrangian best after 30 cold-start iters | $1,953,561 |
| Lagrangian best after 50 iters total (cold + warm) | **$1,885,043** |
| Rollout teacher (validity floor) | $1,273,395 |
| **Tightness vs LP** | **20.7 % tighter** |
| Validity (bound ≥ rollout) | PASS |

The bound effectively converged in the iter 40-50 range, oscillating in
the $1.885 M – $1.897 M band. Phase 1 exit criterion (≥ 20 % tighter
than LP) is met.

Implementation lives in `scripts/run_lagrangian_bound.py`. Key design:
forward enumeration of per-truck DP states with **bucket-snapped Pareto
pruning** — clocks rounded down to each bucket's favorable corner so the
per-truck DP can only over-estimate $V_k^\lambda$, preserving the
upper-bound guarantee. Transitions inline `feas.plan_schedule` and
`feas.realized_profit` to keep per-truck numerics bit-aligned with the
closed-loop simulator. Bucket granularity: 15-min time buckets, 1-hour
HOS drive/duty buckets. The bucketed solver is ~5× faster than the
equivalent non-bucketed Pareto pruning on small scenarios (verified
numerically identical on 30×300×5 iters). The script supports warm-start
via `--initial-duals-csv` and `--iter-offset`, and prints LP-tightness
and rollout-validity comparisons in the report when references are
supplied via `--lp-bound-reference` and `--rollout-reference`.

Phase 1 milestone: fully met. Ready to integrate the Lagrangian-bound
result into the v0.3 paper's Hindsight Ceilings section and proceed to
Phase 2 (Theorem 2: cascade regret bound).


This document defines the work required to convert the current v0.3 paper
draft from a benchmark-with-empirical-comparison artifact into an OR
methodology paper suitable for submission to Transportation Science (or,
secondarily, EJOR / Naval Research Logistics). It supersedes
`freightbidbench_v03_workplan.md` for the methodology track; the existing
workplan remains the reference for the benchmark release itself.

## 1. Objective

Place the v0.3 paper at an INFORMS journal — primary target
Transportation Science, fallback EJOR. Acceptance is not guaranteed at
either venue; the workplan optimizes for **a submission that would clear
desk review and reach the referee stage** at TransSci, with the
expectation that one major revision cycle is likely.

The paper will be repositioned around two theoretical contributions in
addition to the benchmark artifact:

- **Theorem 1.** A Lagrangian-per-truck information relaxation
  producing a substantially tighter full-horizon upper bound than the
  current LP relaxation, derived via Adelman & Mersereau (2008) machinery
  adapted to the FreightBidBench MDP.
- **Theorem 2.** A regret bound for the surrogate-rollout cascade
  characterizing the cascade's performance as a function of the
  surrogate's disagreement set with the rollout teacher, with consequent
  oracle-band and latency-regret-tradeoff results.

Together these convert §5 and §6 from descriptive sections into
methodological contributions; the benchmark and empirical work become
evidence for the theorems rather than the headline content.

## 2. Realistic venue probabilities

| Venue | Acceptance probability after Path B completion |
| --- | --- |
| Transportation Science | medium (35-50%) given a successful Theorem 1 implementation |
| Operations Research | low (5-15%); requires fundamental novelty beyond Path B's scope |
| Management Science | very low; not the right venue |
| EJOR | medium-high (55-70%) |
| Naval Research Logistics | medium-high (55-70%) |
| Transportation Research Part E | high (75-90%) |
| Computers & Operations Research | very high (90%+) |

The submission strategy is: **submit to TransSci first.** If rejected
with referee comments, revise and submit to EJOR or NRL. The work done
for TransSci dominates any other venue's requirements.

## 3. Paper-level positioning

The repositioned abstract should claim, in order:

1. **Benchmark.** A public-calibrated, dependency-free, closed-loop
   benchmark for online truckload bid acceptance, with explicit
   operational feasibility and three new economic layers.
2. **Bound.** A Lagrangian-per-truck information relaxation yielding a
   tight full-horizon upper bound. Empirically, rollout retains
   $\approx X\%$ of the Lagrangian bound on `scarce` (vs. 39.8% of the
   current LP bound), characterizing structural headroom for methods
   work.
3. **Cascade theory.** A regret bound for the surrogate-rollout cascade,
   identifying an oracle band $\beta^\star$ that minimizes regret
   subject to a latency budget. The bound explains the empirically
   observed scenario asymmetry in best cascade-band selection.
4. **Empirical demonstration.** A 30-seed rerun with paired-bootstrap
   confidence intervals showing the cascade recovers $\geq Y\%$ of
   rollout value at $Z\%$ lower latency on both tight and scarce.

The phrase "benchmark contribution" is no longer load-bearing; the paper
sells primarily on the methodology, with the benchmark as the artifact
that enables the methodology to be evaluated.

## 4. Theorem 1 — Lagrangian-per-truck information relaxation

### 4.1 Construction

Let $V^\star$ denote the optimal expected closed-loop reward of the
joint MDP defined in §3 of the paper. The joint problem can be written
as
$$
V^\star = \sup_{a \in \mathcal{A}} \mathbb{E}\Bigl[ \textstyle\sum_t r_t(s_t, a_t) + \Phi(F_T) \Bigr]
\quad \text{subject to} \quad \textstyle\sum_k a^{(k)}_t \leq 1 \text{ for each tendered load } t,
$$
where $a^{(k)}_t \in \{0, 1\}$ indicates whether truck $k$ is assigned
to load $t$ under action $a_t$, and the reward $r_t$ decomposes as
$r_t = \sum_k r^{(k)}_t a^{(k)}_t$ where $r^{(k)}_t$ is truck $k$'s
realized per-load profit (or, on infeasible accept, the service-failure
penalty $-\rho$).

Introduce non-negative duals $\boldsymbol{\lambda} = \{\lambda_t \geq 0\}$ on
the assignment constraints and form the Lagrangian
$$
L(\boldsymbol{\lambda})
= \sup_a \mathbb{E}\Bigl[ \textstyle\sum_t r_t - \textstyle\sum_t \lambda_t (\textstyle\sum_k a^{(k)}_t - 1) + \Phi(F_T)\Bigr]
= \textstyle\sum_t \lambda_t + \textstyle\sum_k V^k_{\boldsymbol{\lambda}}(u^{(k)}_0)
$$
where the per-truck sub-MDP value
$$
V^k_{\boldsymbol{\lambda}}(u^{(k)}_0) = \sup_{a^{(k)}} \mathbb{E}\Bigl[ \textstyle\sum_t a^{(k)}_t (r^{(k)}_t - \lambda_t) + \omega V(\ell^{(k)}_T) \Bigr]
$$
is the optimal value of truck $k$'s independent sub-MDP under the dual
penalty schedule $\boldsymbol{\lambda}$.

### 4.2 Statement of Theorem 1

**Theorem 1 (Lagrangian-per-truck upper bound).** *For any
$\boldsymbol{\lambda} \in \mathbb{R}_{\geq 0}^{|T|}$,
$V^\star \leq L(\boldsymbol{\lambda})$. Consequently
$V^\star \leq \min_{\boldsymbol{\lambda} \geq 0} L(\boldsymbol{\lambda})$, and
the dual minimum is attained at some $\boldsymbol{\lambda}^\star$ since
$L$ is convex and proper.*

### 4.3 Proof sketch

Weak duality: for any $\boldsymbol{\lambda} \geq 0$, the Lagrangian
$L(\boldsymbol{\lambda})$ relaxes the assignment constraint by penalty
rather than enforcement; the supremum over assignments without the
constraint is at least the supremum over feasible assignments.
Decomposability of the reward and the action space across trucks (each
truck's decisions $a^{(k)}$ depend only on $u^{(k)}$ and the realized
load stream, not on other trucks) lets the joint supremum split into a
sum of per-truck suprema. Convexity of $L$ in $\boldsymbol{\lambda}$
follows from the standard pointwise-supremum-of-affine argument.

### 4.4 Why this is a real contribution

The current relaxed bound in §5.2 drops three constraints simultaneously
(integrality, sequencing, location) and gets a bound that is loose by
roughly 2.5× on `scarce`. The Lagrangian-per-truck bound respects:

- Per-truck HOS sequencing (each truck's sub-MDP enforces drive-time
  and duty-time clocks).
- Per-truck location continuity (each truck's geographic trajectory is
  intact).
- Per-truck integrality (a single truck cannot fractionally accept).

What it relaxes is only the *cross-truck* assignment constraint, the
loosest part of the current bound. Empirically, this should tighten the
bound substantially. On comparable weakly-coupled stochastic DPs in the
literature (Adelman & Mersereau 2008, Topaloglu & Powell 2006), the
Lagrangian dual typically captures 60-90% of the integrality gap on the
LP relaxation.

### 4.5 Implementation plan

The implementation is a new script
`scripts/run_lagrangian_bound.py` with the following components.

**Per-truck sub-MDP solver.** For a given $\boldsymbol{\lambda}$:

- State: $(\text{market}, \text{available-time bucket}, \text{drive-time bucket}, \text{duty-time bucket})$.
  Discretize time buckets at 15-minute resolution → state space size on
  order $12 \times 288 \times 12 \times 14 \approx 5.8 \times 10^5$ per
  truck. With sparser bucketing (1-hour drive, 1-hour duty) the size
  drops by 10×.
- Action: at each load arrival affecting the truck's market, accept or
  reject under penalty $\lambda_t$.
- Transition: deterministic post-decision under realized yard delays.
  For the upper bound, we can sample yard delays once per Monte Carlo
  draw of the load stream.
- Solve via backward dynamic programming on the time-indexed state
  space. Per-truck solve: seconds to minutes on a single thread.

**Subgradient dual loop.** Given the per-truck solutions for each
truck, compute the constraint violation
$g_t = \sum_k a^{(k)}_t(\boldsymbol{\lambda}) - 1$ (expected over
scenarios) and step
$\lambda_t \leftarrow \max(0, \lambda_t + \alpha_n g_t)$ with diminishing
step $\alpha_n = c / \sqrt{n}$. Terminate on dual-gap stabilization or
fixed iteration budget (target: 100-300 iterations).

**Monte Carlo dual evaluation.** For each $\boldsymbol{\lambda}$,
evaluate the bound on $M = 30$ realized scenarios, average. The
realized scenarios reuse the same seed pairs as the methods benchmark.

**Output:** `benchmark_runs/v03_sweeps/lagrangian_bound/{scenario}/`
with the converged $\boldsymbol{\lambda}^\star$, the per-seed bound, and
the rollout-vs-bound retention.

**Estimated implementation effort:** 4-6 weeks of focused work,
including tuning and validation against the existing LP relaxation as a
sanity-check upper bound on the Lagrangian bound.

### 4.6 Empirical validation

The headline figure for Theorem 1 is the new Table 4 in the paper:

| Scenario | LP relaxation (current) | Lagrangian bound (Theorem 1) | Rollout retention vs Lagrangian |
| --- | --- | --- | --- |
| `tight`  | \$2,377,500 | $X_1$ | $Y_1$\% |
| `scarce` | \$2,675,525 | $X_2$ | $Y_2$\% |

Expected outcome: $X_1, X_2$ should be 25-50% smaller than the LP
numbers, and rollout retention against $X$ should jump from the current
$\sim$50% / 40% range to a 70-85% range. If rollout retention exceeds
90%, the bound is informatively tight; if it remains below 50%, the
bound is still loose and a further tightening (Section 4.7 below) is
warranted.

**Decomposition.** Replace the current Remark on looseness components
with measured numbers: report how much each successive relaxation
(integrality only, sequencing only, location only, terminal only)
contributes to the LP-bound looseness, by solving intermediate
relaxations. This makes the relaxed-bound decomposition section a real
result rather than an asserted one.

### 4.7 Risk register for Theorem 1

| Risk | Probability | Mitigation |
| --- | --- | --- |
| Dual gap remains large after Lagrangian relaxation | medium | Strengthen with time-bucketed multipliers (one $\lambda$ per (load-bucket, market) pair); add information-relaxation penalty in the BSS sense |
| Per-truck sub-MDP state space too large for backward DP | medium | Sparser time bucketing; aggregate by HOS budget remaining; or replace exact DP with value-function approximation (linear in features) |
| Subgradient convergence is slow | low | Switch to bundle method or accelerated dual methods |
| Bound construction has a hidden flaw at the formal level | low | Internal proof review; sanity check that bound $\geq$ rollout on all seeds |
| Implementation complexity exceeds 8 weeks | medium | Defer to a stand-alone follow-on paper if bound work hits major obstacle; ship Theorem 2 + empirical work for an intermediate-venue submission |

The most important hedge: **if Theorem 1's bound is not materially
tighter than the LP bound after 4 weeks of work, switch to the
information-relaxation-with-non-zero-penalty construction.** This is the
other half of the Brown/Smith/Sun (2010) framework and is
mechanically simpler to implement (the penalty is derived from rollout
value estimates). It typically produces tight bounds when the rollout
teacher is reasonably accurate.

## 5. Theorem 2 — Cascade regret bound

### 5.1 Construction

Recall the cascade $\pi^{\beta,\kappa}_\theta$ defined in the paper.
Define:

- $\pi^R(s)$: the rollout teacher's preferred action at state $s$.
- $\pi^S_\theta(s)$: the surrogate's preferred action (including
  feasibility guard).
- $\mathcal{D} := \{s : \pi^R(s) \neq \pi^S_\theta(s)\}$: the
  disagreement set.
- $R(s) := V^R(s, \pi^R(s)) - V^R(s, \pi^S_\theta(s))$: the
  per-decision regret of using the surrogate's action instead of
  rollout's, evaluated under rollout's expected value.

Note $R(s) \geq 0$ for $s \in \mathcal{D}$ and $R(s) = 0$ for
$s \notin \mathcal{D}$.

### 5.2 Statement of Theorem 2

**Theorem 2 (Cascade regret bound).** *Assume the rollout teacher's
value function is consistent with the closed-loop reward in the sense
that $V^R$ correctly evaluates expected reward under the rollout
policy. Then for any $(\beta, \kappa) \geq 0$,
$$
V^R - V^{\beta, \kappa}_\theta = \mathbb{E}_s\Bigl[\,R(s) \cdot \mathbf{1}\{E(s; \beta, \kappa) = 0\} \cdot \mathbf{1}\{s \in \mathcal{D}\}\Bigr].
$$
Under finite rollout-label budget the equality becomes an inequality
with an additive Monte Carlo variance term of order $O(\sigma_R / \sqrt{M})$
where $\sigma_R$ is the per-decision rollout variance and $M$ is the
label budget.*

### 5.3 Proof sketch

Partition the state space at decision time into three regions:

- $\{E(s) = 1\}$: cascade follows rollout → contributes 0 to regret.
- $\{E(s) = 0\} \cap \{s \notin \mathcal{D}\}$: surrogate and rollout
  agree on action → contributes 0 to regret.
- $\{E(s) = 0\} \cap \{s \in \mathcal{D}\}$: cascade follows surrogate,
  which disagrees with rollout → contributes $R(s)$ to regret.

Summing gives the equality. The Monte Carlo term comes from finite
sample size in computing $V^R(s, a)$ during rollout.

### 5.4 Consequences

**Corollary 1 (Oracle band).** Define the oracle escalation set
$\beta^\star(\theta, \kappa) := \inf\{\beta : \mathcal{D} \subseteq \{s : |\Delta_\theta(s)| \leq \beta\} \cup \{n_o(s) \leq \kappa\}\}$.
At $\beta = \beta^\star$, the cascade incurs zero regret against the
rollout teacher. For $\beta < \beta^\star$, the regret is bounded by
the integral of $R(s)$ over the uncovered subset of $\mathcal{D}$.

**Corollary 2 (Latency-regret Pareto frontier).** Define the cascade's
expected latency as $L(\beta, \kappa) = (1 - \varphi(\beta, \kappa))L_S + \varphi(\beta, \kappa)L_R$
(as in Proposition 3 in the paper). For any latency budget $L_0 \geq L_S$,
the minimum achievable regret subject to $L(\beta, \kappa) \leq L_0$ is
non-increasing in $L_0$, with discrete kinks at $L_0$ values
corresponding to coverage thresholds of $\mathcal{D}$.

**Corollary 3 (Design rule).** The cascade hyperparameters $(\beta, \kappa)$
should be chosen to cover $\mathcal{D}$, not arbitrary cost-margin
distances. In practice, $\mathcal{D}$ is estimated from training data
by recording the states where the trained surrogate disagrees with the
rollout teacher; the released cascade's hyperparameters should then be
set to match the empirical $\mathcal{D}$ distribution.

### 5.5 Why this is a real contribution

Cascade classifiers and surrogate-rollout architectures have appeared
in the ML and OR literatures since at least Viola & Jones (2001) and
the anytime-algorithm work of Boddy & Dean (1989). What is missing in
that literature, for stochastic decision problems specifically, is a
characterization of *which* decisions should be escalated and why.
Theorem 2 answers this for the FreightBidBench cascade: escalate the
states where the surrogate disagrees with the rollout teacher, and no
others. The oracle band $\beta^\star$ makes this design principle
operational.

This is also the result that *explains* the empirical scenario
asymmetry already in the paper (tight prefers $\beta = \$0$, scarce
prefers $\beta = \$700$): on tight, the scarcity trigger alone covers
most of $\mathcal{D}$; on scarce, $\mathcal{D}$ extends beyond the
scarcity regime.

### 5.6 Implementation plan

Theorem 2's bound is mostly mechanical to derive but the empirical
validation requires:

**Disagreement-set characterization.** Augment the cascade evaluation
to record per-decision tuples $(s, \pi^S_\theta(s), \pi^R(s), |\Delta_\theta(s)|, n_o(s))$.
Compute the empirical distribution of $\mathcal{D}$ over the held-out
seed pairs. Stratify by $(|\Delta_\theta|, n_o)$ bins.

**Oracle-band computation.** For each seed pair, compute the minimum
$\beta$ such that $\mathcal{D}$ is covered by the union of the
boundary band and the scarcity trigger at $\kappa = 2$. Average over
seed pairs.

**Cascade-at-oracle-band empirical run.** Run the cascade at the
computed $\beta^\star$ and report its retention and latency against
the standard cascade-band sweep. This validates the bound's prediction.

**New tables in the paper.**

| New table | Content |
| --- | --- |
| Disagreement-set distribution | Cumulative coverage of $\mathcal{D}$ as a function of $\beta$, by scenario |
| Oracle-band comparison | Cascade at $\beta^\star$ vs. cascade at released $\beta$ (88.9%, 99.9%, 98.0%, etc.) |
| Latency-regret Pareto frontier | Pareto-front pairs of (latency, retention) over the $(\beta, \kappa)$ grid |

**Estimated implementation effort:** 2-4 weeks. The bound proof is half
a page; the empirical validation is the main work.

### 5.7 Risk register for Theorem 2

| Risk | Probability | Mitigation |
| --- | --- | --- |
| Empirical oracle band performance fails to dominate the released band | low | Investigate the source of the gap; likely a Monte Carlo or training-data effect |
| Disagreement set is too small to be informative | low | Increase rollout label budget to expand the disagreement set; report sensitivity to label budget |
| Theorem statement reviewer-pushback on equality vs inequality | low | Defensive framing: state the inequality form first, the equality form as a corollary under unbiased rollout |
| Corollary 2 (Pareto frontier) requires regularity assumptions not stated | low | Tighten the corollary statement; verify monotonicity empirically |

## 6. Empirical program

The empirical program for Path B is substantially larger than for the
current draft. Plan for the following runs in sequence; each is gated
by the prior run's success.

### 6.1 Methods table rerun

Target: 30 paired seed pairs across `mild`, `tight`, `scarce` scenarios.

```
python3 scripts/run_freightbidbench.py \
  --config configs/freightbidbench_v03_scenarios.json \
  --preset paper --scenarios mild,tight,scarce \
  --seed-count 30 --label-limit 600 \
  --cascade-bands 0,100,250,500,700,900,1200 \
  --output-dir benchmark_runs/v03_sweeps/methods_paper_seed30_label600
```

Estimated runtime: 20-40 hours on a single thread. With seed-level
parallelism across 8 threads, 3-5 hours.

Mandatory deliverables from this run:
- Paired-bootstrap CI95 for every retention number.
- Paired-seed sign-test p-values for cascade-vs-rollout comparisons.
- `mild` scenario reinstated as a negative control showing it remains
  flat under v0.3 economics.
- Layer-ablation rerun at the same seed count.

### 6.2 Cascade trigger ablation

Add the following cascade variants to the methods table:

- $(\beta=0, \kappa=0)$: pure surrogate (per Theorem 2 Corollary 3).
- $(\beta=0, \kappa=2)$: scarcity-trigger-only (current "band 0").
- $(\beta=500, \kappa=0)$: boundary-trigger-only.
- $(\beta=500, \kappa=2)$: balanced.
- $(\beta=\beta^\star, \kappa=2)$: oracle band (per Theorem 2 Corollary 1).
- $(\beta=\infty, \kappa=0)$: pure rollout.

This sub-table converts the §8.3 interpretive claim about each
trigger's contribution into empirical evidence.

### 6.3 Sensitivity sweeps

Add a $\kappa$ sensitivity row to Table 5 (or its successor), sweeping
$\kappa \in \{0, 1, 2, 4, 8\}$ at $\beta = 500$. Expected outcome: gate
met for $\kappa \in \{2, 4, 8\}$, possibly missed for $\kappa \in \{0, 1\}$.

Add an L3 amplitude sensitivity row at finer granularity:
$\text{amp} \in \{0, 0.125, 0.25, 0.5, 0.75\}$.

### 6.4 Hindsight diagnostics expansion

Extend the exact small-prefix DP table to cover `tight` and `scarce` at
$L \in \{8, 12, 16\}$. Total of 6 rows in the new Table 3.

Add the Lagrangian-bound table (per Section 4.6 above) as the new
full-horizon ceiling.

### 6.5 Lagrangian-bound implementation runs

Per Section 4.5 above. Solver tuning iterations should run on `tight`
first (smaller fleet) before extending to `scarce`. Plan for 1-2 weeks
of solver-tuning runtime in addition to the 4-6 weeks of implementation
work.

### 6.6 Statistical protocol

All headline retention claims must include:
- Mean across seed pairs.
- Paired-bootstrap CI95 (10,000 resamples).
- Sample size $n$.
- Sign-test p-value for the central comparison (cascade vs rollout,
  layer-on vs layer-off, etc.).

Drop point estimates from the abstract; replace with CI-anchored
claims. For example: "cascade recovers 99.9% (CI95: 98.7-100.2%) of
rollout value on `tight`" instead of "at least 98 percent".

## 7. Calibration validation appendix (new)

The single largest unforced error in the current draft is that
"public-calibrated" is asserted but never validated. Path B closes this
with a new Appendix B containing the following:

### 7.1 Load-mix calibration

For each scenario, plot the simulated load-attribute distributions
against published FAF lane-share statistics and USDA AMS truck-rate
distributions. Specifically:

- Origin-state market shares vs. FAF outbound flow shares (12-state
  panel).
- Lane mileage distribution vs. FAF tonnage-weighted mileage
  distribution.
- Linehaul price distribution vs. USDA AMS truck-rate report ranges.

### 7.2 Operational-metric calibration

The simulated fleet's realized operational metrics should resemble
public carrier benchmarks:

- Realized accept-rate distribution vs. ATRI carrier-survey acceptance
  rates.
- Realized deadhead-mile percentage vs. ATRI deadhead figures.
- Realized HOS-rest hours vs. FMCSA aggregate driver-hour reports.

Cite the data sources explicitly. ATRI publishes annual Truckload
Operations reports; FMCSA publishes aggregate HOS compliance data.

### 7.3 Sensitivity to calibration choices

For each calibration parameter that involves a modeling decision (yard
delay distribution, load arrival rate, fleet initialization), report
results at two alternative settings to show that the qualitative
ordering of policies is preserved.

### 7.4 What calibration validation buys

For the paper's external validity, calibration validation is the
strongest single addition. It converts the "synthetic but public-
calibrated" framing from assertion to evidence and pre-empts the most
common referee comment for benchmark papers.

## 8. Rigor cleanup checklist

These are small individually but cumulative. Each is half-a-day to one
day of work.

| Item | Section | Description |
| --- | --- | --- |
| Define $V(\cdot)$ | §3.3 | One equation deriving the state-value signal from FAF outbound intensity and the imbalance table |
| Specify feasibility tie-break | §3.2 | State explicitly which truck the feasibility map selects when multiple are feasible (earliest-available or lowest-deadhead) |
| Specify surrogate training | §6.1 | Ridge regularization $\lambda$, feature standardization protocol, train/eval split, target normalization |
| Resolve $\omega$ collision | §3.3, Prop 1, Prop 2 | Use $\xi$ for random scenario; keep $\omega$ for terminal value weight |
| Resolve $\ell$ overload | §3.1 | Rename load tuple to $\xi_t$ or use a more distinct symbol |
| Rewrite Prop 1 | §4.1 | Demote to remark or replace with a non-trivial identifiability/regret result |
| Rewrite Prop 3(a) proof | §6.2 | Use rollout-rejects-on-empty argument instead of "vanishing probability under mixing" |
| Tighten Prop 3 continuity assumption | §6.2 | Acknowledge atoms from binary/integer features; weaken statement to "agrees a.e. on continuous subspace" |
| Replace weak cascade citations | §2 | Drop Derrow-Pinion ETA and Alonso-Mora ride-pooling; add Viola & Jones (2001), Boddy & Dean (1989), Zilberstein (1996), Horvitz (1987) |
| Reinstate `mild` numerically | §8 | Include `mild` rows in layer ablation, methods, and sensitivity tables |
| Notation table | §3.5 or appendix | Tabular summary of all symbols |

## 9. Literature expansion

The related-work section needs deeper engagement with the OR
literature. Plan to add the following lines of work explicitly:

- **Approximate dynamic programming for transportation:** Powell &
  Topaloglu series (2003 onwards), Topaloglu & Powell (2006) on
  multi-commodity flow, Powell et al. (2014) on locomotive
  optimization, Bouzaiene-Ayari et al. on driver dispatch.
- **Dual-based bounds for stochastic DPs:** Adelman & Mersereau (2008),
  Brown & Haugh (2017), Glasserman & Yu (2004) on duality in optimal
  stopping, Mak, Morton & Wood (1999) on sampled-scenario bounds.
- **Information relaxation:** Brown, Smith & Sun (2010), Lai & Wang
  (2013), Brown & Smith (2014) on dynamic-programming duality.
- **Anytime algorithms and deliberation control:** Boddy & Dean (1989),
  Zilberstein (1996), Horvitz (1987-1989), Russell & Wefald (1991).
- **Cascade classifiers in ML:** Viola & Jones (2001), Saberian & Vasconcelos
  on boosted cascades.
- **Truckload network and bid management:** Crainic et al. on freight
  network design, Erera et al. on truckload brokerage, Powell et al.
  earlier truckload work (1995, 1998).
- **Public OR benchmark culture:** Solomon (1987), Li & Lim (2003),
  Gehring & Homberger (2005), Uchoa et al. (2017), CVRPLIB.

Target: ~50-60 references in the final paper, up from the current ~25.

## 10. Sequencing and milestones

Path B execution divides into four phases. Each phase has a clear exit
criterion.

### Phase 1: Theorem 1 prototype (weeks 1-6)

- Build `scripts/run_lagrangian_bound.py` per Section 4.5.
- Implement per-truck sub-MDP solver with backward DP.
- Implement subgradient dual loop.
- Verify on `tight` scenario at single seed; bound must satisfy
  $L(\boldsymbol{\lambda}) \geq V^R$ (rollout) for sanity.

**Exit criterion:** Lagrangian bound on `tight` is $\geq 20\%$ tighter
than the current LP bound at a single seed. If this fails after 4
weeks, switch to information-relaxation-with-penalty fallback (Section
4.7).

### Phase 2: Theorem 2 derivation + empirical (weeks 5-9, overlapping)

- Write Theorem 2's statement, proof, and corollaries.
- Implement disagreement-set extraction and oracle-band computation.
- Run cascade at $\beta^\star$ on `tight` and `scarce` at single seed
  for validation.

**Exit criterion:** Empirical cascade-at-$\beta^\star$ retention is
$\geq$ retention of the best released $\beta$ at the same scenario, on
at least one scenario.

### Phase 3: Empirical program (weeks 8-14, overlapping)

- 30-seed methods rerun.
- Cascade trigger ablation.
- $\kappa$ and amplitude sensitivity sweeps.
- Hindsight diagnostics expansion.
- Lagrangian-bound multi-scenario runs.

**Exit criterion:** All headline tables have CI95, sign-test
p-values, and $n = 30$ across `tight` and `scarce` (plus `mild` as
negative control).

### Phase 4: Calibration validation, rigor cleanup, paper rewrite (weeks 12-20, overlapping)

- Calibration validation appendix (Section 7).
- Rigor cleanup checklist (Section 8).
- Related-work expansion (Section 9).
- Full paper rewrite at journal length (target: 30-40 pages including
  appendices).
- Internal review cycle and revision.

**Exit criterion:** Paper ready for submission per the TransSci
submission checklist.

### Phase 5: Submission and review cycle (months 5-18)

- TransSci submission.
- Likely outcome: at least one major revision request, possibly two.
- Backup target: if rejected from TransSci, revise to EJOR or NRL
  within four weeks; the same paper should clear desk review at either.

## 11. Risk register (summary)

| Phase | Highest risk | Mitigation |
| --- | --- | --- |
| Phase 1 | Lagrangian bound not materially tighter than LP relaxation | Switch to information-relaxation-with-penalty (Section 4.7) |
| Phase 2 | Oracle band doesn't dominate released band empirically | Investigate; report as "the released cascade is near-oracle on these scenarios" — still a positive result |
| Phase 3 | Statistical results don't survive 30-seed rerun | Either accept the lower numbers honestly, or examine whether the qualitative ordering survives |
| Phase 4 | Calibration plots show large discrepancies with public benchmarks | Document the discrepancies honestly; recalibrate where possible; cite as limitation otherwise |
| Phase 5 | TransSci desk-rejects on methodology grounds | Submit to EJOR/NRL with minor revisions |

## 12. Out of scope for v0.3 / Path B

The following items are tempting but should be explicitly *not* in scope:

- **Stronger ML methods (gradient-boosted, neural surrogate).** These
  break the dependency-free identity and should be a stretch track in
  v0.4.
- **Multi-leg / continuous-move planning.** A separate problem; v0.4 or
  later.
- **Real (private) tender data.** Out of scope; requires a separate
  paper and partner.
- **Dynamic pricing.** Not the accept/reject problem; out of scope.
- **Per-failure-mode service-failure penalty.** L1 scalar penalty is
  sufficient for v0.3; per-failure-mode is v0.4.
- **Adaptive cascade-band selection.** A v0.4 methodology; v0.3 reports
  the fixed-band frontier.
- **Online surrogate adaptation.** A different problem class; v0.5 or
  later.

Holding the line on what is *not* in v0.3 / Path B is as important as
what is in scope. Each excluded item is a paper of its own.

## 13. Decision points

The workplan has two binding decision points that should be revisited
explicitly:

**Decision point 1 (end of week 4): Theorem 1 viability.**
If the Lagrangian bound at week 4 is $\geq 20\%$ tighter than the LP
bound on `tight`, continue with Theorem 1 as planned. If not, the
options are:

- (A) Continue Theorem 1 development for 2-4 more weeks if the
  trajectory is promising.
- (B) Switch to information-relaxation-with-penalty as Theorem 1's
  bound; this is mechanically simpler and typically tighter when the
  rollout teacher's value function is accurate.
- (C) Drop Theorem 1 and submit to a lower-tier venue (Path A) with
  the empirical and Theorem 2 work alone.

**Decision point 2 (end of week 12): submission target.**
If Phase 1-3 have produced strong results and a clean Lagrangian
bound, submit to TransSci. If Phase 1 succeeded but only at the
fallback information-relaxation-with-penalty level, evaluate whether
the methodology is strong enough for TransSci or whether EJOR/NRL is
the right target.

These are not just calendar gates — they are decisions about whether to
escalate effort or pivot to a less ambitious venue. Make them
deliberately rather than letting work drift.

## 14. Estimated total effort

- **Coding and runtime:** 12-16 weeks of focused work, distributable
  across calendar weeks 1-20.
- **Writing:** 4-6 weeks of paper-rewriting work, overlapping Phase 4.
- **Review cycle:** 6-12 months from first submission to acceptance,
  with 1-2 revision cycles likely.
- **Calendar total:** approximately 5 months of work to submission,
  12-18 months to acceptance.

Path B is a real research investment. The current v0.3 release is the
foundation; the v0.3 paper at TransSci is the structure being built on
that foundation.
