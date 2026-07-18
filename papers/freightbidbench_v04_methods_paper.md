# Certified-Gap Dual-Price Policies for Real-Time Truckload Bid Acceptance with Relocating, Clock-Constrained Resources

Aswin Chandrasekaran, Bubba AI (aswin@bubba.ai)

Draft v0.2 (full paper). July 2026. Evaluation artifact: FreightBidBench
(`freightbidbench-v0.4-dev`); all values reproduce from
`benchmark_runs/v04_dev/` per Appendix A.

## Abstract

Real-time truckload bid acceptance requires an accept/reject decision
within seconds of each tender, under fleet state, hours-of-service (HOS)
clocks, and appointment windows. We study this problem as a weakly
coupled dynamic program whose resources are *relocating and
clock-constrained*: serving a request executes a controlled state
transition of the resource (new market, depleted clocks), and
request–resource feasibility depends on resource state — a model that
occupancy-based reusable-resource formulations do not cover. We derive a
real-time dual-price policy from the same Lagrangian relaxation that
yields the problem's upper bound, so every run carries a per-instance
*certified optimality gap*. Theoretically: (i) the certificate is valid
for any duals, discretization, and surrogate quality (Theorem A);
(ii) the policy's same-time spatial-gradient form is exactly fluid
complementary slackness, and the policy is asymptotically optimal in the
subcritical fluid regime (Theorem B(i)), with dual prices that are
provably portable across sample paths by LP basis stability; (iii) in
contrast, per-resource Lagrangian slack can remain bounded away from
zero at all fleet sizes — we exhibit a three-truck kernel with an exact
rational certificate and a replication lemma (Theorem B(ii)),
delimiting what certificates can promise under state-dependent
coupling. Empirically, on a public closed-loop benchmark over thirty
paired seeds, the training-free policy matches or beats a
rollout-trained surrogate (tight: +2.0 pp, paired-bootstrap CI95
[+0.5, +3.6]) at 0.04–0.09 ms per decision — three orders of magnitude
below the Monte Carlo rollout teacher — and is certified at a stable
57–64% of optimal across ten independently bounded instances per
scenario, within 3–6 points of what the 1000×-slower rollout teacher
itself certifies.

## 1. Introduction

Truckload carriers and brokers answer a stream of load tenders in real
time. Each acceptance consumes a truck whose future usefulness depends
on where the load delivers it and how much drive and duty time its
driver has left; each rejection preserves options whose value depends on
demand that has not arrived yet. The operational state of the art for
future-aware acceptance is finite-lookahead Monte Carlo rollout, which
is accurate but costs tens to hundreds of milliseconds per decision and
scales poorly with fleet size. The benchmark release preceding this
paper (FreightBidBench v0.3) made the problem reproducible — public
calibration, explicit feasibility, versioned contracts — and supplied
hindsight upper bounds; its best latency-aware method, a
surrogate-to-rollout cascade, recovers ~98% of rollout profit but
inherits rollout's cost on escalated decisions and offers no statement
about distance from *optimal*.

This paper asks the harder question the bounds make precise: **how close
to optimal can a real-time policy be, and can that closeness be
certified per instance?** Our answer exploits a single object twice. The
Lagrangian relaxation that dualizes the one-truck-per-load constraint
yields (a) an upper bound on the optimum — the benchmark's ceiling — and
(b) per-load dual prices and per-market value potentials from which we
build an acceptance policy that runs in microseconds. Because policy and
bound derive from one relaxation, every run ships with an observable
certificate: realized policy value over realized bound.

Pairing a Lagrangian policy with its bound is the standard playbook of
weakly coupled dynamic programs. The contribution here is the model in
which we make it work, the form of the policy, and the two-sided theory
of the certificate:

1. **Model (§2).** Resources whose *service capability is a controlled
   state variable*: state-dependent feasibility (location + HOS clocks
   gate eligibility), controlled relocation (service moves the
   resource), autonomous renewal (rests restore clocks). None of the
   adjacent literatures — classical weakly coupled DPs, online reusable
   resources, dual mirror descent for online allocation — covers this
   combination (§1.1).
2. **Policy and certificate (§3–4).** A dual-price policy whose
   relocation term is a *same-time spatial gradient* of an aggregated
   value surface, plus Theorem A: the certificate is valid for any
   duals, any permissive discretization, and any surrogate quality.
   Lemma A3 isolates the design rule — *duals price time, gradients
   price place* — and we show the naive continuation rule collapses
   (14% of rollout) by double-charging the busy-time cost.
3. **Fluid consistency and portability (§5).** In the subcritical
   regime the gradient rule is exactly fluid complementary slackness
   (Lemma B3: idle potentials are flat), fitted prices converge to
   fluid rents (Lemma B4), and the policy is asymptotically optimal
   (Theorem B(i)). Basis stability further implies the fitted prices
   are *portable across days* — a prediction the benchmark confirms
   (identical decisions under frozen vs fresh duals) — and predicts
   where portability fails.
4. **Limits of the relaxation (§6).** Certificates cannot promise
   everything: we exhibit a three-truck kernel with a certified duality
   gap (exact rational arithmetic; a half-integral chain packing beats
   the integer optimum) and a replication lemma, so per-resource
   Lagrangian slack can stay bounded away from zero at every fleet size
   (Theorem B(ii)). Random search shows such kernels are rare at small
   scale (~0.03%), while the benchmark's proportional-scaling
   experiments show per-resource bound slack *growing* with contention
   density — behavior outside the conditions under which classical
   O(1)-gap results hold.
5. **Evidence (§7).** Thirty paired seeds, paired-bootstrap CIs: the
   training-free policy beats a rollout-trained linear surrogate on the
   tight scenario (+2.0 pp, CI95 [+0.5, +3.6]) and ties it elsewhere,
   at lower latency than the surrogate and ~1000× below rollout;
   certificates over ten independently bounded instances per scenario
   are stable (57–64% of optimal) and within 3–6 points of what rollout
   itself certifies — locating most of the certified gap in the
   relaxation, not the policy.

### 1.1 Related work

**Weakly coupled DPs and bid prices.** Dynamic bid prices from value
approximations originate with Adelman (2007); Lagrangian decompositions
of weakly coupled DPs with policy+bound pairing are standard since
Hawkins (2003), Adelman and Mersereau (2008), and Topaloglu (2009), who
reports bounds and policy values on the same network-RM instances. Our
Theorem A inherits this mechanism; the extension is the resource model
(state-dependent participation, controlled relocation) and the explicit
certificate framing at sub-millisecond decision latency. Brown and Zhang
(2023) bound the ALP–Lagrangian gap by O(1) constants under conditions
on linking constraints that state-dependence violates; Theorem B(ii) and
the scaling experiments exhibit exactly the behavior their conditions
exclude — in the natural freight scaling, constraints number ∝ K and
participation is state-dependent.

**Online reusable resources.** Zhang and Cheung (2022) and the
nonstationary extension in Mathematics of OR (2023+) allocate units that
occupy and *return unchanged*; feasibility is availability-only. A truck
returns elsewhere with depleted clocks. This controlled-relocation
distinction is not cosmetic: it is what makes the chain-packing LP
non-integral (§6) and what the same-time gradient prices (§5).

**Online allocation with dual updates.** Balseiro, Lu, and Mirrokni
(2020) attain optimal O(√T) regret with per-request dual mirror descent
for consumable budgets, motivated by the same latency constraints. We
deliberately make no regret-rate claim — rates are a settled
literature — and instead fix prices offline (portable by Lemma B4),
leaving the online variant to future work.

**Fleet ADP.** Industrial-scale approximate DP for truckload fleets
(Simão et al. 2009; Powell and collaborators) produced marginal values
of driver states as model outputs, aimed at calibration rather than
optimality certification; no per-instance gap reporting appears in this
line.

**Compute-aware deferral.** Value-of-computation metareasoning for
Monte Carlo search (e.g., Sezener and Hutter 2020) has not been applied
to operational dispatch; the benchmark's cascade and this paper's
policy make the freight instantiation available, and we leave a learned
deferral rule to future work.

## 2. Model

### 2.1 Resources, requests, and controlled relocation

Time is continuous on [0, T]. A fleet of K resources (trucks) has states
`x_k = (m_k, τ_k, h_k, d_k) ∈ X`: market `m` in a finite set `M`,
next-available time `τ`, and remaining drive/duty clocks `(h, d)`.
Requests (load tenders) `ℓ_1, …, ℓ_N` arrive at times `t_1 < … < t_N`;
request `ℓ` carries origin `o(ℓ)`, destination `δ(ℓ)`, and the
price/cost/window attributes of the benchmark. Three primitives
distinguish the model from occupancy-based reusable resources:

- **State-dependent feasibility.** A deterministic map `f(x, ℓ) ∈ {0, 1}`
  gates service: `f = 1` only if the resource is in the origin market,
  can reach the pickup inside its appointment window, and admits an
  HOS-feasible schedule through delivery.
- **Controlled relocation.** Serving executes `x ← S(x, ℓ)`: the market
  becomes `δ(ℓ)`, the next-available time advances by the service
  duration including inserted rests, and the clocks are updated by the
  drive/duty consumed. The resource does not return to its prior pool
  state.
- **Autonomous renewal.** Idle resources renew clocks by resting
  (11/14/10 in the benchmark), so service capability regenerates in a
  state-dependent way.

### 2.2 Joint control problem

At each arrival `t` the controller observes `(x_1, …, x_K, ℓ_t)` and
chooses `a_t ∈ {0, 1, …, K}` (reject, or assign to a feasible resource).
Writing `a^{(k)}_t = 1{a_t = k}`, the joint constraint is
`Σ_k a^{(k)}_t ≤ 1`. Rewards follow the benchmark: realized profit
`r(x_k, ℓ_t)` on feasible accepts, service-failure penalty on infeasible
attempts (excluded under `f`-gated policies), terminal fleet value
`Φ = ω Σ_k V(m_k(T))`. `V*(ξ)` is the optimum on realized scenario `ξ`.

### 2.3 Lagrangian per-resource decomposition

Dualizing the joint constraint with prices `λ = (λ_t) ≥ 0`,

    L(λ; ξ) = Σ_t λ_t + Σ_k V^k_λ(x_k(0); ξ),

where `V^k_λ` is resource k's optimal value in its own sub-MDP with
per-service reward `r(x, ℓ_t) − λ_t`, retaining `f`, `S`, and renewal.
Weak duality gives `V*(ξ) ≤ L(λ; ξ)` pointwise for every `λ ≥ 0`. The
benchmark computes `L` by bucketed forward enumeration with a
permissive-corner guarantee, so reported bounds remain valid upper
bounds under discretization; per-resource solves parallelize (stdlib
multiprocessing; bit-identical to serial).

## 3. The Dual-Price Policy

### 3.1 Price and value surrogates

Fix any duals `λ ≥ 0` (in practice: ~15 subgradient iterates on one
training scenario — policy quality saturates well before bound-grade
convergence). Two aggregated objects are fitted offline:

- **A price surface** `λ̂ : M × [0, 24) → R_{≥0}`: the mean dual of
  loads by origin market and hour-of-day — the opportunity cost of
  origin-market capacity-time (Lemma B4 identifies its limit as the
  fluid rent `E[(r − θ)_+]`).
- **An aggregated value-to-go** `Ŵ : M × [0, T] → R`: the backward
  recursion on the (market, hour) grid over the realized train stream
  with dual-netted rewards
  `Ŵ(m, t) = max( Ŵ(m, t+1), max_{ℓ: t_ℓ = t, o(ℓ) = m} [ r̄(ℓ) − λ_{t_ℓ} + Ŵ(δ(ℓ), t + tt(ℓ)) ] )`,
  `Ŵ(m, T) = ω V(m)`.

### 3.2 Policy

On arrival `ℓ` at time `t` with fleet `(x_1, …, x_K)`:

    k* ∈ argmax_{k : f(x_k, ℓ) = 1}  r(x_k, ℓ)
    score = r(x_{k*}, ℓ) − λ̂(o(ℓ), t) + [ Ŵ(δ(ℓ), t + tt(ℓ)) − Ŵ(o(ℓ), t + tt(ℓ)) ]
    accept with k* iff score ≥ 0.

The bracket is the **same-time spatial gradient** — the value of being
at the destination rather than the origin *at the completion time*. The
busy-time opportunity cost is priced once, by `λ̂`. Each decision costs
a feasibility probe over origin-market resources plus two lookups;
measured latency 0.02–0.12 ms across fleet sizes 35–140 versus 32–159 ms
for rollout — an advantage that *widens* with fleet size.

## 4. Certified Gaps

**Theorem A (certified optimality gap).** *Let `λ ≥ 0` be arbitrary and
`π` any feasible policy. On every realized scenario `ξ`,
`V^π(ξ) ≤ V*(ξ) ≤ L(λ; ξ)`, hence the observable
`gap(ξ) := L(λ; ξ) − V^π(ξ)` upper-bounds the true suboptimality
`V*(ξ) − V^π(ξ)`. The certificate remains valid for any `λ`, any
per-resource discretization with the permissive-corner property, and
any quality of `λ̂, Ŵ` — surrogate error degrades policy value (widening
the reported gap) but never invalidates the certificate.*

*Proof.* Left inequality: definition of the optimum. Right: weak
duality (§2.3), pointwise in `ξ`. Subtract. The invariances hold
because the certificate uses only an upper bound computed from
`(λ, ξ)` and the realized value of a feasible policy. ∎

**Proposition A2 (exactness).** *If `λ*` minimizes `L(·; ξ)` and the
per-resource optimizers jointly satisfy primal feasibility and
complementary slackness, the assembled plan is optimal and the
certificate is tight.* (Proof as in the standard weakly-coupled
setting; in practice a residual contested set (~1–2% of loads) keeps
the certificate strictly positive.)

**Lemma A3 (busy-time double-counting).** *In the recursion of §3.1,
`Ŵ(m, t) − Ŵ(m, t')` equals the value of the best dual-netted service
chain departing m within `[t, t')`; hence the naive continuation
`Ŵ(δ, t+tt) − Ŵ(o, t)` subtracts the busy-time opportunity value a
second time on top of `λ̂`, while the same-time gradient prices
relocation alone.* (*Proof:* monotonicity of `Ŵ(m, ·)` plus unrolling
the max branches; the identity
`Ŵ(δ,t+tt) − Ŵ(o,t) = [Ŵ(δ,t+tt) − Ŵ(o,t+tt)] − [Ŵ(o,t) − Ŵ(o,t+tt)]`
is algebraic. ∎) Empirically the naive rule collapses to 14–17% of
rollout profit; the gradient rule attains 90–95% (§7). *Duals price
time; gradients price place.* Lemma B3 upgrades this from a property of
our construction to fluid optimality.

## 5. Fluid Consistency in the Subcritical Regime

### 5.1 Fluid model and its LP

Scale fleet and demand together: `K` resources, lane-ℓ arrivals a
Poisson process of rate `K Λ_ℓ(t)` with mean reward `r̄_ℓ` and travel
time `τ_ℓ`, lane geometry fixed. Normalize per resource. The fluid
control problem routes resource mass over the market–time network:
variables are dispatch rates `u_ℓ(t) ∈ [0, Λ_ℓ(t)]` and idle mass
`z_m(t) ≥ 0`, with flow balance

    ż_m(t) = Σ_{ℓ: δ_ℓ = m} u_ℓ(t − τ_ℓ) − Σ_{ℓ: o_ℓ = m} u_ℓ(t),
    max ∫_0^T Σ_ℓ r̄_ℓ u_ℓ(t) dt + ω Σ_m V(m) z_m(T).

This is a continuous transportation LP; write `V_f` for its value and
`(λ_ℓ(t), w_m(t))` for optimal duals on the arrival-capacity and
flow-balance constraints. Dual feasibility on dispatch and waiting arcs:

    (D1)  w_{o_ℓ}(t) ≥ r̄_ℓ − λ_ℓ(t) + w_{δ_ℓ}(t + τ_ℓ),  eq. on used arcs,
    (D2)  w_m(t) ≥ w_m(t⁺),                                eq. where z_m(t) > 0.

**Assumptions.** (A1) Subcriticality: the fluid optimum keeps
`z_m(t) ≥ z_min > 0` for all m, t. (A2) Clock slack: per-resource
service intensity at the fluid optimum is below the HOS renewal rate,
so clock constraints are non-binding in the limit. (A3) Nondegeneracy:
the fluid LP has a unique dual optimum with finitely many basis-switch
times. (A4) Bounded rewards and travel times; `Λ_ℓ(·)` piecewise
continuous (the benchmark's periodic schedule qualifies).

**Lemma B3 (idle potentials are flat; the gradient rule is fluid-CS).**
*Under (A1), (D2) holds with equality for all m, t: `w_m(·)` is constant
between basis switches, and in particular `w_o(t) = w_o(t + τ)`
whenever idle mass persists at o on `[t, t + τ]`. Consequently the
fluid-optimal acceptance rule "serve lane ℓ at t iff
`r̄_ℓ − λ_ℓ(t) + w_{δ_ℓ}(t+τ_ℓ) − w_{o_ℓ}(t) ≥ 0`" coincides with the
same-time spatial-gradient rule*

    r̄_ℓ − λ_ℓ(t) + [ w_{δ_ℓ}(t + τ_ℓ) − w_{o_ℓ}(t + τ_ℓ) ] ≥ 0,

*and the naive-continuation penalty `w_o(t) − w_o(t + τ)` is exactly the
binding-capacity correction: zero under (A1), strictly positive where
capacity binds.*

*Proof.* Complementary slackness on waiting arcs gives equality in (D2)
wherever `z_m > 0`; under (A1) that is everywhere, so `w_m` is flat in
t. Substituting `w_o(t) = w_o(t+τ_ℓ)` into (D1) yields the displayed
rule. The final claim is the same substitution read in reverse where
`z_o = 0` forces strict inequality in (D2). ∎

Lemma B3 upgrades Lemma A3 from a property of our construction to the
statement that *the same-time gradient is the fluid-optimal rule in the
subcritical regime*, and explains the naive rule's empirical collapse
as a misapplied binding-capacity correction: the v2 policy paid a
congestion price that, at its acceptance margins, belonged to the
single-resource hindsight chain rather than the fleet optimum.

### 5.2 Price consistency and the theorem

**Lemma B4 (dual stability).** *Work with the hourly fluid LP (cells
`(ℓ, h)`; the fitting granularity of λ̂ and Ŵ). Under (A1)–(A4), on a
sample path at scale K: (a) the realized arc-flow LP's node potentials
`ŵ_m(h)` equal the fluid potentials `w_m(h)` with probability
`1 − o(1)`, and its cell thresholds converge at `O_p(K^{-1/2})`;
(b) the bucket-averaged load duals satisfy
`λ̂(ℓ, h) → λ_ℓ(h) := E[(r − θ_{ℓh})_+]` at `O_p(K^{-1/2})`, where
`θ_{ℓh} = w_{o_ℓ}(h) − w_{δ_ℓ}(h + τ_ℓ)` is the fluid acceptance
threshold; (c) the chain-packing duals of Lemma B1 coincide with the
arc-flow duals on an event of probability `1 − o(1)`.*

*Proof.* **(Step 1: cell LP and basis stability.)** Aggregate the
realized instance into cells: `N_{ℓh}` loads arrive in cell `(ℓ, h)`
with i.i.d. rewards; the arc-flow relaxation over the market–hour
network is a finite LP with data `b_K = N/K` (arrival masses) and `c_K`
(mean rewards). By Poisson concentration and the CLT over finitely many
cells, `b_K = b + O_p(K^{-1/2})` and `c_K = c + O_p(K^{-1/2})`. Let
`B*` be the fluid LP's optimal basis, unique and nondegenerate by (A3):
its optimality conditions hold with strict inequality, hence remain
valid on an open neighborhood of `(b, c)`. On the event
`E_K = {(b_K, c_K) in that neighborhood}` — probability `1 − o(1)` —
the realized LP has the same optimal basis. Dual solutions are
functions of the basis and objective only, `y = c_B (B*)^{-1}`: they do
not depend on `b`, so `ŵ_m(h) = w_m(h)` exactly on `E_K` up to the
`O_p(K^{-1/2})` objective perturbation. This proves (a).

**(Step 2: disaggregation.)** In the load-level LP each load i in cell
`(ℓ, h)` has its own capacity constraint with dual `λ_i`. With the
basis fixed, complementary slackness gives `λ_i = (r_i − θ̂_{ℓh})_+`:
loads strictly above threshold are served and earn their surplus as
rent; loads below have slack capacity and zero dual. Averaging over the
`N_{ℓh} = Θ(K)` i.i.d. rewards,
`λ̂(ℓ, h) = mean_i λ_i → E[(r − θ_{ℓh})_+]` by the LLN at rate
`O_p(K^{-1/2})`, using `θ̂ → θ` from (a). This proves (b) and
identifies the fitted price surface's limit as the fluid rent function.

**(Step 3: chains vs flows.)** `conv(chains_k) ⊆ {unit flows from k's
start}`, with equality of optimal values whenever the resource-budget
(clock) side constraints are slack at the flow optimum — which holds
under (A2) on an event of probability `1 − o(1)` (realized service
intensities track fluid intensities by Step 1 + Azuma). On that event
the additional chain constraints are non-binding and both LPs share
optimal duals. This proves (c). ∎

**Remark (portability, explained).** Step 1 says the price surface is a
*basis object*: two independent sample paths yield the same potentials
whenever both land in the stability neighborhood — probability
`(1 − o(1))²`. The empirical portability finding (identical policy
decisions under frozen vs fresh duals) is LP basis stability, not an
accident of the benchmark; and portability should fail near fluid basis
switches (arrival-regime changes), a testable prediction.

**Theorem B(i) (subcritical fluid consistency).** *Under (A1)–(A4), the
dual-price policy `π_λ` built from λ̂, Ŵ fitted on an independent sample
path satisfies*

    V^{π_λ}(K) ≥ V_f · K − o(K)   and   V*(K) ≤ V_f · K + o(K),
    hence  V^{π_λ}(K) / V*(K) → 1.

*Proof (assembly).* Upper bound: the realized instance's optimum is at
most the fluid LP with perturbed arrival counts; Poisson concentration
(Bernstein over lane–hour cells) gives the `o(K)` correction. Lower
bound: by Lemma B4 the fitted surfaces are within `o_p(1)` of the fluid
duals except near finitely many switch times (total measure `o(T)`); by
Lemma B3 the policy's rule then agrees with the fluid-optimal rule
except on (i) switch-time neighborhoods, (ii) decisions with score
within `o_p(1)` of zero (vanishing fluid mass by (A3)), and (iii)
fluctuation events. Under (A1), fleet mass at every origin exceeds
`z_min K − O_p(√K) > 0`, so every fluid-accepted arrival finds a
feasible resource and realized service rates track fluid rates to
`O_p(√K)` (Azuma over arrival blocks; (A2) keeps clocks non-binding).
Summing reward differences over the exception sets gives
`V^{π_λ} ≥ V_f K − o(K)`. ∎

**Remarks.** (a) The critical regime `z_min = 0` (tight/scarce
economics) is genuinely open: (D2) equality fails, the gradient rule
loses its CS status, and §6 shows per-resource duality slack can
persist; we conjecture `V^{π_λ}/V* → 1 − ε(ρ)` with `ε` growing in
contention. (b) Assumption (A2) is where HOS clocks live; relaxing it
requires a regeneration argument at rest events and is this section's
main technical debt.

## 6. Limits of the Relaxation

**Theorem B(ii).** *There exist instance families with
`[min_λ L(λ) − V*] / K ≥ γ > 0` for all fleet sizes K.*

**Lemma B1 (Dantzig–Wolfe equivalence).** *For a realized instance, let
`C_k` denote resource k's finitely many feasible service chains and
`val(S)` a chain's total reward. Then `min_{λ ≥ 0} L(λ)` equals the
chain-packing LP*

    max { Σ_k Σ_{S ∈ C_k} val(S) x_{k,S} :
          Σ_k Σ_{S ∋ t} x_{k,S} ≤ 1 ∀t,  Σ_S x_{k,S} ≤ 1 ∀k,  x ≥ 0 }.

*Proof.* `L(λ) = Σ_t λ_t + Σ_k max_{S ∈ C_k ∪ {∅}} [val(S) − λ(S)]` is
the Lagrangian dual function of the integer chain-packing program; each
inner maximum is over a finite set, so `min_λ L` equals the LP
relaxation over the convex hulls of the per-resource feasible sets
(Dantzig–Wolfe / Geoffrion), which is the displayed column LP. ∎

**Lemma B2 (replication).** *Let `I0` have `k0` resources and duality
gap `g0 = min_λ L(λ; I0) − V*(I0) > 0`. Then `n` disjoint copies
satisfy `V*(I0^n) = n V*(I0)` and `min_λ L(·; I0^n) = n min_λ L(·; I0)`,
hence per-resource slack `g0 / k0 > 0` for every `K = n k0`.*

*Proof.* No chain, constraint, or transition couples distinct copies,
so both the joint DP and the chain-packing LP separate and optima add;
apply Lemma B1 per copy. ∎

**Kernel K1** (exhibited; exact rational certificates via
`scripts/find_gap_kernel.py`): three
resources with staggered availabilities and budget 2, six loads in
cyclic geography; `V* = 41` by joint enumeration while the
half-integral packing `x = 1/2` on
`T0:{L4}, T1:{L2,L3}, T1:{L5}, T2:{L3,L5}, T2:{L1,L4}` is feasible with
value `89/2`, so the certified duality gap is `≥ 7/2` and `γ = 7/6`.
The binding structure — one resource holding two valuable chains it can
execute only once, odd-cyclic overlap through shared loads — is exactly
the structure whose absence provably collapses the gap (identical
loads, one-shot assignment, and exchangeable resources each yield zero
gap). **Remark (rarity and density).** Random micro-instances carry
certified gaps in only ~0.03% of draws — at small scale the relaxation
is almost always tight — while the benchmark's proportional-scaling
experiments show per-resource bound slack growing with density
(+17%/resource from K = 70 to 140, robust to two step-size schedules).
The density-growth characterization is open; the non-contradiction with
Brown–Zhang's O(1) results is that their conditions fix few,
state-independent constraints, whereas here constraints number ∝ K with
state-dependent participation.

## 7. Experiments

All experiments use the public benchmark's frozen `scenario-v0.3.2`
contract, thirty held-out paired seeds (pairs 1–30; the dual tables are
fitted on pair 0's stream and never refitted), paired-bootstrap CI95
(20,000 resamples), and two-sided sign tests. Policies: `bid_price`
(future-value proxy), `surrogate_linear` (ridge on 200 rollout labels
per pair, retrained per pair), `dual_price` (flat-price ablation),
`dual_price_vf` (this paper), `rollout_teacher`.

**Table 1 — retention vs rollout (n = 30).**

| policy | tight | scarce | mild |
| --- | ---: | ---: | ---: |
| bid_price | 91.1% | 85.9% | 99.1% |
| surrogate (200 labels/pair) | 93.4% | 91.1% | 98.3% |
| dual_price (flat ablation) | 91.2% | 86.6% | 99.1% |
| **dual_price_vf (zero labels)** | **95.4%** | **90.0%** | **101.8%** |
| paired vf − surrogate | **+2.0 pp [+0.5, +3.6]** | −1.0 pp [−3.2, +1.3] | **+3.5 pp [+2.4, +4.5]** |
| Wilcoxon signed-rank p | 0.023 | 0.299 | <0.001 |
| latency vf / surrogate / rollout (ms) | 0.059 / 0.081 / 74.5 | 0.040 / 0.075 / 48.0 | 0.090 / 0.106 / 111.7 |

The training-free policy beats the rollout-trained surrogate on tight
(CI excludes zero; 19/30 wins, sign-test p = 0.20 — the edge is in
magnitudes), ties elsewhere, and is faster than the surrogate. The flat
ablation sits at bid-price level: the same-time gradient is the source
of the edge, as Lemma A3/B3 predict.

**Table 2 — per-instance certificates (n = 10 bound-solved instances
per scenario, 45-iteration solves).**

| | dual_price_vf | rollout_teacher |
| --- | ---: | ---: |
| tight | **60.0%** of optimal (56.9–63.6) | 62.8% (60.5–66.8) |
| scarce | **57.5%** (53.4–61.5) | 63.7% (61.2–65.3) |

Certificates are narrow, stable distributions; the 1000×-slower rollout
teacher certifies only 2.8–6.2 pp higher, locating most of the certified
gap in the relaxation — consistent with §6 and with the scaling
diagnosis below.

**Table 3 — proportional fleet scaling (tight economics; equal-
convergence solves; policy-vs-rollout from the scaling diagnostic).**

| K | bound/K | policy/K | policy vs rollout | certified gap |
| ---: | ---: | ---: | ---: | ---: |
| 35 | $26,780 | $17,242 | 116.6% | 35.6% |
| 70 | $26,929 | $16,970 | 93.3% | 37.0% |
| 140 | $31,585 | $15,104 | 96.9% | 52.2% |

The policy is scale-robust against rollout while per-resource bound
slack inflates at 2× density; the level is robust to a 2× step-size
schedule reset (13 aggressive iterations never improve on the
fine-schedule bound). Rollout's latency grows 32 → 159 ms over this
range; the dual policy stays ~0.1 ms.

**Portability and solver budgets.** Decisions are identical under
frozen (pair-0) vs freshly solved (pair-1) duals on both scenarios —
the finite-sample shadow of Lemma B4's basis stability. Policy quality
saturates by ~15 subgradient iterations; bound-grade certificates
require ~45; per-resource solves parallelize at 3.05× on four cores.

## 8. Discussion

**A certificate culture for freight decisioning.** Every policy run on
the benchmark can now report "provably ≥ x% of optimal on this
instance." The certificates are conservative exactly where §6 says they
must be, and the decomposition (policy loss vs relaxation slack) tells
methods researchers where improvement is possible (tighter bounds) and
where it is not (the policy is already near rollout).

**Prices are infrastructure.** Basis stability makes the fitted price
surface a reusable asset: one offline solve prices weeks of operations,
with a testable warning condition (arrival-regime switches) for when to
refit. This is a deployment-relevant property no per-request-learning
scheme offers.

**Where the money is.** The remaining certified gap at scale is
dominated by cross-resource coupling slack that neither faster policies
nor more solver iterations recover; tightening it (chain-aware duals,
restricted exchange constraints) is the natural next methodological
target — and Theorem B(ii)'s kernel families are the test cases.

## 9. Limitations

Certificates inherit the bound's looseness; in the critical regime they
understate policy quality (Table 2's rollout row) and Theorem B(i) does
not apply — the critical case is open. Assumption (A2) folds HOS-clock
renewal into the regime; relaxing it needs a regeneration argument. The
surrogate baseline is the benchmark's dependency-free linear model, not
a tuned learned policy; rollout is the strong baseline. Benchmark
caveats (public calibration, lane concentration) carry over from the
v0.3 release. The online-updating variant and a learned deferral rule
are deferred to future work by scope discipline.

## 10. Conclusion

A single Lagrangian object yields a microsecond, training-free,
portable acceptance policy and a per-instance certificate of its
optimality gap. The theory says precisely when the certificate is tight
(subcritical fluid consistency) and exhibits, with exact certificates,
why it cannot always be (kernels with irreducible per-resource slack).
On a public benchmark the policy matches or beats a rollout-trained
surrogate at three orders of magnitude lower latency than the teacher.
The benchmark, solver, kernel search, and all tables are released for
independent verification.

## Declarations

The author is employed by Bubba AI, which develops AI-based
load-planning and carrier-operations products in the freight domain
addressed by this paper. This study uses only public data and the
open-source benchmark; Bubba AI had no role in study design, analysis,
or the decision to publish. The author used Anthropic's Claude to
assist with software implementation, experiment scaffolding, drafting,
and literature support; all designs, proofs, results, and claims were
verified and approved by the author, who takes full responsibility.

## Appendix A. Reproducibility

Python ≥ 3.10, standard library only. Headline commands: the 30-seed
program (`run_30seed_program.sh`: Phase A policy comparisons via
`scripts/run_dual_price_experiment.py`, Phase B certificates via
`scripts/run_lagrangian_bound.py --workers 4`), price/value fitting
(`scripts/fit_dual_prices.py`, `scripts/fit_value_togo.py`), scaling
cells (`configs/freightbidbench_v04_dev_scaling.json`), kernel search
with exact certificates (`scripts/find_gap_kernel.py`). Artifacts under
`benchmark_runs/v04_dev/`; manifests and per-iteration dual checkpoints
throughout.
