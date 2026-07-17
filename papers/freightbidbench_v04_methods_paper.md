# Certified-Gap Dual-Price Policies for Real-Time Truckload Bid Acceptance with Relocating, Clock-Constrained Resources

Aswin Chandrasekaran, Bubba AI (aswin@bubba.ai)

Draft v0.1 (theory core: model, dual decomposition, policy, Theorem A,
decomposition lemma, Theorem B target). July 2026. Evaluation artifact:
FreightBidBench (`freightbidbench-v0.4-dev`); empirical values below are
from `benchmark_runs/v04_dev/` and will be finalized on the 30-seed
program.

## 1. Introduction (skeleton)

Real-time truckload bid acceptance requires an accept/reject decision
within seconds of each tender. The v0.3 benchmark paper established a
reproducible closed-loop test bed and showed that a surrogate-to-rollout
cascade recovers ~98% of a Monte Carlo rollout teacher's profit at a
fraction of its latency. This paper asks the harder question the
benchmark's hindsight ceilings make precise: *how close is a real-time
policy to optimal, and can that closeness be certified per instance?*

Our answer is a dual-price policy derived from the same
Lagrangian-per-truck relaxation that produces the benchmark's upper
bound. Because policy and bound derive from one object, every run
carries an observable certificate: the realized gap between the bound and
the policy's realized value. The mechanism — pair a Lagrangian
relaxation's heuristic policy with its bound — is the standard playbook
of weakly coupled dynamic programs (Hawkins 2003; Adelman and Mersereau
2008; Topaloglu 2009). The contribution here is its extension to a
resource model that this literature, and the more recent online
reusable-resource literature, does not cover: resources whose *service
capability is itself a controlled state variable*.

**Positioning (one paragraph per lane).** (i) Classical weakly coupled
DPs and network revenue management assume linking constraints whose
participation does not depend on subproblem state; here, whether truck k
can serve load t depends on k's location and hours-of-service clocks.
(ii) The online reusable-resource literature (Zhang and Cheung 2022;
nonstationary variants, Math. OR 2023+) models units that occupy and
return to an unchanged pool; a truck returns *elsewhere, with depleted
clocks* — a controlled relocation, not an occupancy. (iii) Dual mirror
descent for online allocation (Balseiro, Lu, Mirrokni 2020) supplies the
online-update template but prices consumable budgets, not
state-transitioning resources. (iv) Brown and Zhang (2023) bound the
ALP–Lagrangian relaxation gap by an O(1) constant *under conditions on
the linking constraints that state-dependence violates*; our scaling
experiments exhibit exactly the gap growth their conditions rule out.

## 2. Model

### 2.1 Resources, requests, and controlled relocation

Time is continuous on [0, T]. A fleet of K resources (trucks) has states
`x_k = (m_k, τ_k, h_k, d_k) ∈ X`: market `m` in a finite set `M`,
next-available time `τ`, and remaining drive/duty clocks `(h, d)`.
Requests (load tenders) `ℓ_1, …, ℓ_N` arrive at times
`t_1 < … < t_N`; request `ℓ_t` carries origin `o(ℓ)`, destination
`δ(ℓ)`, and the price/cost/window attributes of the benchmark.

Three primitives distinguish the model from occupancy-based reusable
resources:

- **State-dependent feasibility.** A deterministic map
  `f(x, ℓ) ∈ {0, 1}` gates service: `f = 1` only if the resource is in
  the origin market, can reach the pickup inside its appointment window,
  and admits an HOS-feasible schedule through delivery.
- **Controlled relocation.** Serving executes a state transition
  `x ← S(x, ℓ)`: the market becomes `δ(ℓ)`, the next-available time
  advances by the (stochastic) service duration including any inserted
  rests, and the clocks are updated by the drive/duty consumed. The
  resource does not return to its prior pool state.
- **Autonomous renewal.** Idle resources renew clocks by resting
  (11/14/10 in the benchmark), so service capability regenerates in a
  state-dependent way.

### 2.2 Joint control problem

At each arrival `t`, the controller observes `(x_1, …, x_K, ℓ_t)` and
chooses `a_t ∈ {0, 1, …, K}` (reject, or assign to resource `a_t` with
`f(x_{a_t}, ℓ_t) = 1`). Writing `a^{(k)}_t = 1{a_t = k}`, the joint
constraint is `Σ_k a^{(k)}_t ≤ 1` for every `t`. Rewards follow the
benchmark: realized profit `r(x_k, ℓ_t)` on feasible accepts, `−ρ` on
infeasible accept attempts (excluded by construction under `f`-gated
policies), terminal fleet value `Φ = ω Σ_k V(m_k(T))`. The optimal value
on a realized scenario `ξ` (a common-random-number sample path) is
`V*(ξ)`; the closed-loop optimum is `V* = E[V*(ξ)]`.

### 2.3 Lagrangian per-resource decomposition

Dualizing only the joint constraint with prices `λ = (λ_t)_{t≤N} ≥ 0`,

    L(λ; ξ) = Σ_t λ_t + Σ_k V^k_λ(x_k(0); ξ),

where `V^k_λ` is resource k's optimal value in its own sub-MDP with
per-service reward `r(x, ℓ_t) − λ_t`, retaining `f`, `S`, and renewal.
Weak duality gives `V*(ξ) ≤ L(λ; ξ)` for every `λ ≥ 0` pointwise in `ξ`
(v0.3 paper, Prop. 3; standard). The benchmark computes `L` by bucketed
forward enumeration with a permissive-corner guarantee, so reported
bounds remain valid upper bounds under discretization.

## 3. The Dual-Price Policy

### 3.1 Price and value surrogates

Fix any duals `λ ≥ 0` (in practice: subgradient iterates on one training
scenario). Two aggregated objects are fitted offline from `(λ, ξ_train)`:

- **A price surface** `λ̂ : M × [0, 24) → R_{≥0}`, the mean dual of
  loads by origin market and hour-of-day — the opportunity cost of
  consuming a unit of origin-market capacity-time.
- **An aggregated value-to-go** `Ŵ : M × [0, T] → R`, the backward
  Bellman recursion on the (market, hour) grid over the realized train
  stream with dual-netted rewards:
  `Ŵ(m, T) = ω V(m)`;
  `Ŵ(m, t) = max( Ŵ(m, t+1), max_{ℓ: t_ℓ = t, o(ℓ) = m} [ r̄(ℓ) − λ_{t_ℓ} + Ŵ(δ(ℓ), t + tt(ℓ)) ] )`,
  with `r̄` the fresh-resource profit and `tt` the service duration.

### 3.2 Policy definition

On arrival `ℓ` at time `t` with fleet `(x_1, …, x_K)`:

    k* ∈ argmax_{k : f(x_k, ℓ) = 1}  r(x_k, ℓ)
    score(ℓ, t) = r(x_{k*}, ℓ) − λ̂(o(ℓ), t) + [ Ŵ(δ(ℓ), t + tt(ℓ)) − Ŵ(o(ℓ), t + tt(ℓ)) ]
    π_λ accepts with k* iff score ≥ 0; otherwise rejects.

The bracketed term is the **same-time spatial gradient**: the value of
*being at the destination rather than the origin at the completion
time*. The busy-time opportunity cost — what the resource forgoes while
serving — is priced once, by `λ̂`. Section 4.3 shows that pricing it
twice (the naive continuation `Ŵ(δ, t+tt) − Ŵ(o, t)`) collapses the
policy. Each decision costs O(#resources in the origin market) probe
work plus two table lookups; measured latency is 0.02–0.12 ms across
fleet sizes 35–140, versus 32–159 ms for the rollout teacher.

## 4. Theorem A: Certified Gaps

**Theorem A (certified optimality gap).** *Let `λ ≥ 0` be arbitrary and
let `π` be any feasible policy (in particular `π_λ`). On every realized
scenario `ξ`,*

    V^π(ξ)  ≤  V*(ξ)  ≤  L(λ; ξ),

*and therefore the observable quantity
`gap(ξ) := L(λ; ξ) − V^π(ξ)` satisfies*

    V*(ξ) − V^π(ξ)  ≤  gap(ξ).

*The policy's true suboptimality on the instance is certified by
`gap(ξ)` without knowledge of `V*`. Moreover the certificate is valid
for any `λ`, any discretization of the per-resource solves satisfying
the permissive-corner property, and any quality of `λ̂, Ŵ` — surrogate
error degrades policy value (and hence widens the reported gap) but
never invalidates the certificate.*

*Proof.* The left inequality is the definition of the optimum on `ξ`.
The right inequality is weak duality for the dualized joint constraint
(§2.3), valid pointwise in `ξ` for every `λ ≥ 0`. Subtracting `V^π(ξ)`
from both sides of `V*(ξ) ≤ L(λ; ξ)` gives the display. The final claims
follow because the certificate uses only (i) an upper bound computed
from `(λ, ξ)` — whose validity is independent of how `λ` was chosen —
and (ii) the realized value of a feasible policy. ∎

**Remark (tightness anatomy).** `gap(ξ)` decomposes as
`[L(λ; ξ) − V*(ξ)] + [V*(ξ) − V^{π_λ}(ξ)]`: dual slack plus policy
loss. The scaling experiments of §6 estimate the two parts separately by
using the rollout teacher as a strong feasible yardstick: policy loss vs
rollout stays small (≤ 7 pp across a 4× fleet range) while dual slack
grows with density — the growth is a property of the relaxation, not of
the policy.

**Proposition A2 (exactness at zero duality gap).** *Suppose `λ*`
attains `min_λ L(λ; ξ)` and the per-resource optimizers under `λ*`
jointly satisfy the primal constraint (`Σ_k a^{(k)*}_t ≤ 1` for all t)
and complementary slackness (`λ*_t (Σ_k a^{(k)*}_t − 1) = 0`). Then the
joint plan assembled from the per-resource optimizers is optimal on `ξ`
and `gap(ξ) = 0` when `π` implements it.*

*Proof.* Under primal feasibility and complementary slackness the
Lagrangian value equals the assembled plan's primal value:
`L(λ*; ξ) = Σ_t λ*_t + Σ_k [r-terms − λ*-terms] = primal value`, since
the dual charges net out exactly on served loads and vanish on unserved
ones. A feasible primal plan whose value equals an upper bound is
optimal. ∎

In practice the relaxed solution over-uses a residual set of contested
loads (~1–2% of the stream in the benchmark), so A2 identifies the
certificate's slack source rather than a typically-attained state.

### 4.3 The decomposition lemma (why the spatial gradient is correct)

**Lemma A3 (busy-time double-counting).** *In the aggregated recursion
of §3.1, for any market `m` and `t ≤ t' ≤ T`,*

    Ŵ(m, t) − Ŵ(m, t')  =  value of the best dual-netted service chain
                            departing m within [t, t'),  (≥ 0)

*i.e. the temporal decline of `Ŵ` at a fixed market equals the
opportunity value of the capacity-time consumed — the same quantity the
duals price on the contested stream. Consequently the naive continuation*

    Ŵ(δ(ℓ), t + tt) − Ŵ(o(ℓ), t)
      = [ Ŵ(δ(ℓ), t + tt) − Ŵ(o(ℓ), t + tt) ]  −  [ Ŵ(o(ℓ), t) − Ŵ(o(ℓ), t + tt) ]

*subtracts the busy-time opportunity value a second time on top of
`λ̂`, and any policy using it under-accepts whenever chains are long
(the single-resource hindsight value of the remaining stream), while
the same-time gradient prices relocation alone.*

*Proof.* By induction on the recursion: `Ŵ(m, ·)` is non-increasing
(the wait branch gives `Ŵ(m, t) ≥ Ŵ(m, t+1)`), and unrolling the max
branches over `[t, t')` expresses the difference as the best dual-netted
chain departing within the window, which is nonnegative and zero iff no
chain improves on waiting. The displayed identity is algebraic. ∎

Empirically the naive continuation collapses acceptance to 14–17% of
rollout profit while the same-time gradient attains 91–95%; Lemma A3 is
the formal content of that observation, and we propose it as the design
rule for value-function bid prices over relocating resources: *duals
price time, gradients price place.*

### 4.4 Empirical instantiation (30 held-out seed pairs)

Thirty held-out seed pairs, frozen single-stream duals
(`benchmark_runs/v04_dev/seed30/`): retention vs rollout 95.4% (tight),
90.0% (scarce), 99.2% (mild, negative control). Paired against a
rollout-label-trained linear surrogate (200 labels per pair), the
zero-label dual policy is **better on tight** (+2.0 pp, paired-bootstrap
CI95 [+0.5, +3.6], 19/30 wins, sign-test p = 0.20) and statistically
indistinguishable on scarce (−1.0 pp, CI95 [−3.2, +1.3]) and mild
(+0.8 pp, CI95 [−0.3, +2.0]) — at lower latency than the surrogate
(0.04–0.09 ms vs 0.08–0.11 ms) and three orders of magnitude below
rollout (48–112 ms). The flat-price ablation (`dual_price`, no value
gradient) sits at bid-price level (91.2% / 86.6%), isolating the
same-time spatial gradient as the source of the edge, as Lemma A3
predicts. Certificates on the bound-solved stream: ≥ 63.0% (tight),
≥ 55.5% (scarce) of optimal; per-instance certificate distributions over
ten seeds per scenario are computed by the Phase-B program. Price
portability: decisions identical under frozen vs fresh duals; policy
quality saturates by ~15 subgradient iterations (bound-grade ~45+).

## 5. Online Variant (section stub — Theorem C target)

Per-decision multiplicative update of `λ̂(m, hour)` buckets from
observed contention, no training scenario. Target result: sublinear
regret vs the offline-dual benchmark under the benchmark's periodic
arrival modulation, positioned as a structural extension (relocation +
state-dependent feasibility) of dual mirror descent, not a rate
improvement. Deferred until Theorem B's analysis fixes the fluid-limit
machinery.

## 6. Theorem B target: scaling and the limits of the relaxation

Empirical basis (proportional scaling of fleet and arrivals, tight
economics, equal-convergence solves):

| K | bound/K | policy/K | policy vs rollout | rel. certified gap |
| ---: | ---: | ---: | ---: | ---: |
| 35 | $26,780 | $17,242 | 116.6% | 35.6% |
| 70 | $26,929 | $16,970 | 93.3% | 37.0% |
| 140 | $31,585 | $15,104 | 96.9% | 52.2% |

Two robustness checks pin the K = 140 gap growth on the relaxation:
(i) policy loss vs the rollout teacher does not grow (96.9%); (ii) the
bound level is schedule-robust — a fine-step schedule asymptotes to
$4.42M and an aggressive reset schedule (2× step) never finds lower
ground in 13 iterations (oscillates $4.55–5.0M) — so the slack is not
recoverable dual optimization at reasonable budgets.

**Theorem B (target statement, two parts).**
*(i) (Policy consistency.) Under proportional scaling `(K, N) → ∞` with
fixed lane geometry and mixing conditions on renewal and arrivals, the
dual-price policy's per-resource value converges to the per-resource
fluid optimum (equivalently `V^{π_λ}/V* → 1` in the fluid limit).*
*(ii) (Relaxation gap growth under state-dependent coupling.) There
exist instances of the model — and the benchmark's proportional-scaling
family exhibits the behavior — in which the per-resource Lagrangian
slack `[L(λ*) − V*]/K` is bounded away from zero and increasing in
contention density, in contrast to the O(1) total-gap guarantees
available when linking-constraint participation is state-independent
(Brown–Zhang conditions).*

Proof strategy for (i): fluid relaxation of the aggregated recursion;
couple `π_λ` to the fluid solution via the same-time gradient (Lemma A3
supplies the exchange argument); concentration over i.i.d. arrival
blocks; regeneration at rest events to break clock coupling. Stated for
the subcritical regime; the critical-regime question is left open (see
working note). For (ii): **existence is established** — an exact search
(`scripts/find_gap_kernel.py`, certificates in rational arithmetic via a
chain-packing LP equal to `min_λ L` by Dantzig–Wolfe) exhibits kernels
with certified duality gaps up to 8.5% of `V*`, realized by cyclic
geography, staggered availabilities, and budget-limited chaining; a
replication lemma extends any kernel to per-resource slack bounded away
from zero for all K. Kernels are rare at small scale (~0.03% of random
instances), which the paper reports as a finding in itself; the
density-growth refinement is the remaining open piece.

## 7. Experiments plan (30-seed program, per workplan §5)

Headline: policies × {mild, tight, scarce} × 30 paired seeds with CI95;
certified-gap table per scenario; latency frontier with the dual policy
as the sub-millisecond extreme point; dual+VOC cascade vs v0.3 threshold
cascade; scaling table above re-run at 3 seeds per cell; portability and
solver-budget tables.

## Declarations

Competing interest and AI-use acknowledgments carry over verbatim from
the v0.3 paper.
