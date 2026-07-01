# Latency-Aware Bid Acceptance under Operational Feasibility: A Public Benchmark with Hindsight Ceilings

Aswin Chandrasekaran, Bubba AI (aswin@bubba.ai)

Code and benchmark artifacts: <https://github.com/aswincsekar/freightbidbench>
Artifact release: `freightbidbench-v0.3`, scenario contract `scenario-v0.3.2`,
policy set `policy-set-v0.3.0`. July 2026.

## Abstract

Online truckload bid acceptance is a closed-loop stochastic decision problem
in which a carrier or broker must, in real time, accept or reject a tendered
load subject to operational feasibility, fleet repositioning costs, and
opportunity cost against future demand. Public, reproducible benchmarks for
this problem are scarce: existing routing benchmarks are static, while
dynamic-fleet studies typically rely on private operator data. We introduce
FreightBidBench, a public-calibrated, dependency-free, closed-loop benchmark
in which feasibility (pickup reach, appointment windows, simplified
hours-of-service, stochastic yard delays) and economics (service-failure
penalty, terminal fleet value, daily price-premium window) are explicit,
versioned, and reproducible from public Freight Analysis Framework and
U.S. Department of Agriculture truck-rate data.

Building on this benchmark, we make three contributions. First, we
formalize the v0.3 closed-loop accept/reject MDP and show that the three
new reward components each isolate a distinct policy class: a service-
failure penalty creates linear regret for feasibility-blind policies,
terminal fleet value penalizes greedy positioning, and a temporal
price-premium window penalizes future-blind timing. Second, we develop
three complementary hindsight diagnostics: an exact realized-seed
dynamic program for small load prefixes, a simple LP-style full-horizon
upper bound, and a Lagrangian-per-truck information-relaxation bound
that retains per-truck HOS and sequencing structure and is 20.7%
tighter than the LP relaxation on `tight` and 39.3% tighter on `scarce`
while remaining dependency-free, justified as an information relaxation
in the sense of Brown, Smith, and Sun. Third, we introduce a parametric
surrogate-rollout cascade with two escalation triggers — a boundary band
β ≥ 0 on the surrogate's signed score and a scarcity-pressure threshold
κ on the count of immediately available trucks in the origin market —
characterize its limit behaviour (rollout-call share monotone in either
trigger threshold), and show that the scarcity trigger alone captures
the high-stakes capacity decisions on which the surrogate is least
reliable.

On ten-seed tight and scarce scenarios, the best simple policy retains
91.0% and 86.5% of rollout profit, respectively, and a stdlib linear
surrogate 94.2% and 89.3%; a cascade at a single escalation band
recovers ~98% on both at 40–56% of rollout's mean decision latency,
and on `tight` is statistically indistinguishable from the rollout
teacher (paired-bootstrap 95% CI on the profit delta spans zero).
The release contains a versioned manifest, layer ablations, sensitivity
sweeps, and an exact-plus-relaxed ceiling, providing a reproducible test
bed for future methods work.

## 1. Introduction

Truckload carriers and brokers face an online accept/reject decision each
time a load tender arrives. The decision is constrained by latency:
tenders in a typical broker workflow must be priced and accepted or
rejected within seconds. The decision is operationally constrained: a
load can only be served by a truck that can reach the pickup, satisfies
appointment windows and hours-of-service (HOS) clocks, and remains
feasible through delivery. The decision is economically constrained: a
tender with positive immediate margin can still be a poor decision if it
consumes a scarce truck before a predictable price-premium window or
strands the fleet in a market with weak outbound flow. Conversely, no
benchmark can claim to compare future-aware acceptance policies
meaningfully unless it (a) makes operational feasibility part of the
reward function rather than a side diagnostic, and (b) anchors policy
evaluation against a measured ceiling rather than only against a finite
stochastic rollout teacher.

Existing routing benchmarks, such as the Solomon and Homberger–Gehring
VRPTW instances and the CVRPLIB tradition, anchor the static
vehicle-routing literature but are not closed-loop and do not model
online stochastic tender arrivals. Stochastic and dynamic vehicle-routing
surveys (Pillac et al., Ritzinger et al.) document the distinction
between offline policy construction and online computation, while
fleet-management approximate dynamic programming (ADP) work (Simão et
al., Powell et al., Topaloglu and Powell) has historically been driven
by private operator data. Recent stochastic VRP benchmarks (Heakl et
al.) target a different problem geometry (multi-customer routing) than
online truckload bid acceptance. The closed-loop, fleet-state-dependent,
latency-aware truckload accept/reject problem with public calibration
has lacked a shared reproducible artifact.

FreightBidBench v0.2 took a first step by adding operational feasibility
(per-truck records, pickup reach time, appointment windows, simplified
11/14/10 HOS, stochastic yard delays) to a public-calibrated benchmark
built on the Freight Analysis Framework and U.S. Department of
Agriculture truck-rate reports. That release showed that feasibility is
first-order: ignoring HOS or appointment windows materially changes
which policies look competitive. However, the v0.2 economic structure
was too flat for a credible methods claim: simple greedy baselines and
the finite rollout teacher were often within a few percentage points of
each other, leaving no room for cheaper future-aware approximations to
demonstrate value.

The present paper, anchored on the v0.3 release of FreightBidBench,
addresses three gaps. We sharpen the benchmark economics so that the
decision problem has provable structural separation between feasibility-
blind, future-blind, and future-aware policies; we anchor policy
comparison against both an exact small-prefix dynamic program and a
dependency-free relaxed full-horizon upper bound; and we introduce a
parametric latency-aware policy class that interpolates between a cheap
surrogate and a finite rollout teacher. Throughout, the benchmark is the
primary artifact: the methods results are evidence that the sharpened
problem admits a non-trivial latency-profit frontier, but the benchmark
stands as a reproducible test bed independent of any specific method.

Our contributions are as follows. We formalize the v0.3 closed-loop MDP
and prove that each of three new reward components (service-failure
penalty, terminal fleet value, temporal price-premium window) separates
a distinct class of policies that any future-aware method must beat. We
characterize two complementary full-horizon upper bounds: a simple
LP-style relaxation that drops integrality, sequencing, and location
constraints, and a tighter Lagrangian-per-truck information relaxation
that dualizes only the cross-truck assignment constraint and retains
per-truck HOS, location, and sequencing structure. We decompose the LP
looseness into positioning, sequencing, and integrality components and
show that the Lagrangian bound recovers most of the sequencing and
integrality slack. We define a surrogate-rollout
cascade as a parametric policy class with boundary-band and
scarcity-pressure escalation triggers, prove its limit behaviour, and
provide a structural justification for the scenario-dependent
calibration that we observe empirically. Finally, we release the benchmark with
versioned scenario, policy, and feasibility contracts; a manifest-based
reproducibility protocol; layer-ablation and sensitivity experiments;
and exact-plus-relaxed hindsight ceilings.

## 2. Related Work

**Dynamic truckload fleet management and bid acceptance.** Dynamic load
acceptance and rejection in truckload operations has been formulated as
an online state-dependent control problem since at least Kim,
Mahmassani, and Jaillet, who study large-fleet acceptance with priority
demand and time windows. Yang, Jaillet, and Mahmassani study real-time
multi-vehicle truckload pickup and delivery and develop online
reoptimization heuristics. Tjokroamidjojo, Kutanoglu, and Taylor
quantify the value of advance load information in truckload trucking.
The ADP-based fleet-management line, beginning with Simão et al. and
surveyed in Powell, Simão, and Bouzaiene-Ayari, established that
state-dependent value-function approximation can match operator-scale
fleet decisions. Subsequent applications include locomotive optimization
(Powell et al.) and time-staged integer multi-commodity flow (Topaloglu
and Powell). FreightBidBench complements this line by providing a
reproducible benchmark on which policies of varying complexity can be
compared under shared stochastic seeds.

**Stochastic and dynamic vehicle routing.** Surveys by Pillac et al. and
Ritzinger et al. catalogue dynamic and stochastic vehicle-routing
problems and the distinction between offline policy construction and
online computation. Ulmer et al. develop offline–online ADP and
meso-parametric value-function approximations for dynamic customer
acceptance. Secomandi and Margot study reoptimization for the VRP with
stochastic demands. These works motivate the rollout teacher and
surrogate tracks in FreightBidBench. The benchmark gap is that truckload
bid evaluation also requires public freight calibration, fleet
repositioning under operational feasibility, and latency-profit
reporting — none of which are first-class in static VRPTW instance sets.

**Hindsight bounds and information relaxation.** Anchoring policy
evaluation against an upper bound is a long-standing theme in stochastic
dynamic programming. Brown, Smith, and Sun develop a general
information-relaxation duality framework that gives upper bounds on
stochastic-DP optima by giving the decision maker access to future
information offset by an optional penalty. Adelman and Mersereau develop
Lagrangian relaxations for weakly coupled stochastic dynamic programs.
Both lines justify reporting a ceiling alongside achievable policies. We
adopt the information-relaxation framing for the v0.3 relaxed
full-horizon bound and report it explicitly as a (loose) upper bound
rather than a feasible plan. The exact realized-seed dynamic program we
report on small load prefixes serves as the trustworthy reference
against which the relaxation can be calibrated.

**Rollout policies and cascades.** Rollout, introduced for combinatorial
optimization by Bertsekas, Tsitsiklis, and Wu and extended for
finite-horizon stochastic DPs by Goodson, Thomas, and Ohlmann, is the
methodological lineage of the v0.3 rollout teacher: common-random-number
Monte Carlo expansion of accept and reject branches, with the better
expected branch chosen. Rollout is accurate but computationally
expensive. Cascading a cheap surrogate to an expensive teacher,
escalating only when the surrogate is uncertain, instantiates two older
ideas: cascade classifiers, which route easy instances through cheap
stages and hard instances to expensive stages (Viola and Jones), and
anytime algorithms and metareasoning, which allocate computation
according to its expected value (Boddy and Dean; Zilberstein; Russell
and Wefald; Horvitz). What is missing for stochastic decision problems
is a systematic benchmark of such cascades under public calibration with
operational feasibility. The v0.3 paper formalizes the cascade as a
parametric policy class indexed by escalation triggers and reports its
frontier on the public benchmark.

**Learning-augmented routing.** Recent learning-augmented optimization
studies use neural or attention-based policies to accelerate routing
decisions (Nazari et al., Kool et al., Patel et al.). We intentionally
keep the v0.3 reference implementation dependency-free so that the
benchmark itself remains reproducible from the Python standard library;
optional learned baselines are deferred to a stretch track in future
releases.

**Public benchmarks in OR.** Static benchmark instances have shaped
routing research for decades (Solomon, Homberger and Gehring, Uchoa et
al.). Recent stochastic routing benchmarks (Heakl et al.) push toward
dynamic settings but target multi-customer pickup-and-delivery rather
than online truckload bid acceptance. FreightBidBench fills the latter
gap with versioned scenario, policy, and feasibility contracts and a
manifest-based reproducibility protocol.

## 3. Problem Formulation

We formalize closed-loop truckload bid acceptance as a finite-horizon
Markov decision process with continuous time-stamped events.

### 3.1 State and Action

The horizon is `T = 72` hours. The fleet consists of `K` trucks, each
with state `u^(k)_t = (l^(k)_t, tau^(k)_t, h^(k)_t, d^(k)_t)` where
`l^(k)_t` is the truck's market (state), `tau^(k)_t` is the next
available time, `h^(k)_t` is the remaining HOS drive-time budget, and
`d^(k)_t` is the remaining HOS duty-time budget. The fleet state is
`F_t = (u^(1)_t, ..., u^(K)_t)`.

A load tender event at time `t` presents a candidate load with attributes
`(o, d, p, c_lin, m, tau_pe, tau_pl, tau_de, tau_dl, Y_p, Y_d)`: origin
and destination markets, posted price after the temporal premium,
linehaul cost, mileage, pickup and delivery appointment window endpoints,
and stochastic yard-delay draws at pickup and dropoff. The system state
is `s_t = (F_t, load_t, t)` and the action space is binary,
`a_t ∈ {0, 1}`.

### 3.2 Feasibility Layer

A deterministic feasibility map attempts to assign the load to a truck.
The candidate set is the trucks currently located in the load's origin
market. For each candidate the map computes pickup-reach time,
pickup-arrival including yard delay, drive time, HOS rest insertions if
required, and delivery-arrival including yard delay. Candidates whose
next-available time already exceeds the load's latest pickup are dropped
before scheduling. Among the candidates that admit an HOS-feasible
schedule, the map selects the truck that becomes available earliest after
completing the load — i.e. it minimizes the post-delivery next-available
time `tau^(k)` — with ties broken by fleet index order. The map returns
either the assigned truck and updated fleet state (`ok`), or, if no
candidate is feasible, the unchanged fleet state (`infeasible`).

### 3.3 Reward

For `a_t = 1` with feasibility flag `ok`, the realized reward is
`p − c_lin − c_ph · m_dh − c_Y · (Y_p + Y_d)`, where `c_ph` is the cost
per deadhead mile, `m_dh` is the pickup-reach mileage from the assigned
truck, and `c_Y` is the per-hour yard-delay cost. For `a_t = 1` with
feasibility flag `infeasible`, the fleet is not mutated and the reward
is `−ρ`, where `ρ ≥ 0` is the v0.3 service-failure penalty. For
`a_t = 0`, the reward is zero.

At the horizon the system collects a terminal fleet reward
`Φ(F_T) = ω · Σ_k V(l^(k)_T)`, where `V(·)` is a state-value signal
derived from FAF outbound intensity and the USDA AMS imbalance table,
and `ω ≥ 0` is the v0.3 terminal value weight.

The state-value signal is computed once per scenario from public data.
Let `b(ℓ)` be state `ℓ`'s FAF outbound tonnage and `g(ℓ)` its net
outbound-tonnage imbalance from the 2024 FAF/USDA imbalance table.
Define the [−1, 1]-scaled outbound intensity
`b̂(ℓ) = 2 b(ℓ) / max_j b(j) − 1` and the scaled imbalance
`ĝ(ℓ) = g(ℓ) / max_j |g(j)|`. Then

`V(ℓ) = σ · ( 0.70 · b̂(ℓ) + 0.30 · ĝ(ℓ) )`,

where `σ` is the scenario's terminal value scale (`value_scale_dollars`,
$2,400/$3,000/$3,400 for `mild`/`tight`/`scarce`). The 0.70/0.30 split
weights raw outbound demand above the directional imbalance correction.

### 3.4 Objective

A policy is a mapping from state to action probability. The closed-loop
objective is to maximize expected total reward, including terminal
fleet value, under the joint distribution of load arrivals (Poisson with
hour-of-day modulated rate), candidate-load draws from the
public-calibrated lane table, and yard-delay distributions. We compare
policies under common random numbers: for a fixed (train seed, eval
seed) pair, load streams, yard delays, and initial fleet positions are
identical across all policies.

### 3.5 Notation

| Symbol | Meaning |
| --- | --- |
| `T` | horizon length (72 h) |
| `K` | fleet size (trucks) |
| `ξ` | a realized scenario (one common-random-number sample path) |
| `F_t`, `u^(k)_t` | fleet state at time `t`; truck `k`'s state |
| `ℓ^(k)_t`, `τ^(k)_t` | truck `k`'s market and next-available time |
| `h^(k)_t`, `d^(k)_t` | truck `k`'s remaining HOS drive / duty budgets |
| `s_t = (F_t, load_t, t)` | system state; `load_t` is the tendered load |
| `a_t ∈ {0,1}` | accept/reject action |
| `ρ` | service-failure penalty (L1), $10 |
| `ω` | terminal fleet-value weight (L2), 0.25 |
| `V(ℓ)` | per-market terminal state-value signal (§3.3) |
| `σ` | scenario terminal value scale (`value_scale_dollars`) |
| `μ(t)` | temporal price multiplier (L3) |
| `V^π`, `V*` | expected closed-loop value of policy `π`; optimum `sup_π V^π` |
| `U^R(ξ)` | relaxed full-horizon upper bound on scenario `ξ` |
| `L(λ)`, `λ_t` | Lagrangian bound; per-load assignment dual |
| `Δ_θ(s)` | surrogate signed accept-minus-reject score |
| `β`, `κ` | cascade boundary band; scarcity threshold |
| `n_o(s)` | trucks in the origin market immediately available at `t` |
| `φ(β,κ)` | cascade rollout-call share |

## 4. Benchmark Economics in v0.3

The v0.3 release introduces three reward components on top of the v0.2
feasibility-aware MDP. Each component is independently controllable
through the versioned scenario contract
`configs/freightbidbench_v03_scenarios.json`, currently frozen at
`scenario-v0.3.2`.

### 4.1 L1: Service-Failure Penalty

A policy that accepts a load classified as infeasible incurs reward
`−ρ`; the fleet is not mutated. In v0.2, `ρ = 0`; in v0.3, `ρ = $10`
after calibration.

**Proposition 1 (Feasibility-blind regret under L1).** Let `π` be a
policy that does not consult the feasibility map before accepting, and
let `π'` be its feasibility-aware variant. Let `N(π, ξ)` denote the
realized number of infeasible accepts of `π` on scenario `ξ`. Then
`V^{π'} − V^{π} = ρ · E[N(π, ξ)]`.

*Proof.* `π` and `π'` agree on every decision except infeasible
attempts. Fleet state is not mutated on infeasible accepts, so they
have identical fleet trajectories and identical realized rewards except
that `π` pays `−ρ` per infeasible-accept event while `π'` pays zero.

Proposition 1 establishes that `ρ > 0` creates linear regret in the
realized infeasible-accept count. The frozen value `ρ = $10` is the
smallest tested value that flips `myopic_margin` and `bid_price` below
`accept_all_feasible` on both `tight` and `scarce`.

### 4.2 L2: Terminal Fleet Value

End-of-horizon trucks receive value `ω · V(l^(k)_T)`, with `ω = 0.25`
in `scenario-v0.3.2`. This term penalizes policies that strand trucks
in low-value markets at horizon end. Unlike L1, L2 acts on policies
that respect feasibility but are myopic with respect to terminal
positioning. The feasibility-aware greedy baseline `accept_all_feasible`
loses retention against rollout under L2 because it accepts the first
feasible load without consideration of where the truck ends.

### 4.3 L3: Temporal Price-Premium Window

The frozen demand-wave schedule keeps the load-arrival rate flat and
applies a daily price multiplier `μ(t) = 1.5` during hours `[8, 16)`
and `μ(t) = 1.0` otherwise. The schedule creates a controlled timing
problem: accepting a moderate off-peak load can consume capacity
required for a predictable on-peak premium. L3 separates future-blind-
on-timing policies from future-aware policies that can reason about
premium-window saturation.

### 4.4 Versioned Artifacts

The v0.2 reference run remains immutable under
`benchmark_runs/paper_v02/`; the v0.3 scenario contract lives in
`configs/freightbidbench_v03_scenarios.json`; and v0.3 table drafts and
ceilings are assembled under `benchmark_runs/paper_v03/`.

## 5. Hindsight Ceilings

### 5.1 Exact Small-Prefix Dynamic Program

For a truncated realized stream of `L` loads, the exact problem is a
binary decision tree of depth `L` over the deterministic
post-acceptance fleet transition. We solve it by memoized search keyed
on (prefix index, fleet hash). The state count grows exponentially in
`L` but the deterministic assignment rule and small fleet keep the
search tractable for `L ≤ 16` on the v0.3 scenarios.

### 5.2 Relaxed Full-Horizon Upper Bound

For the full horizon, we report the minimum of two upper bounds plus a
terminal upper bound:

- **Positive-profit relaxation.** Accept every realized load with
  positive fresh-truck profit, ignoring fleet location, sequencing, and
  capacity.
- **Fractional truck-hour relaxation.** Ignore location and sequencing,
  charge each profitable load a lower-bound busy time, and solve the
  resulting fractional truck-hour knapsack.

Both bounds additively include a terminal upper bound that allows every
truck to end in the highest-value market.

**Proposition 2 (Validity of the relaxed bound).** Let `U^R(ξ)` denote
the relaxed full-horizon objective evaluated on realized scenario `ξ`.
Then `E[U^R(ξ)] ≥ V*`, where `V* = sup_π V^π`.

*Proof sketch.* `U^R` is constructed by (i) revealing the full
realized scenario in advance — a zero-penalty information relaxation
in the sense of Brown, Smith, and Sun — (ii) replacing the integer
truck-assignment constraint by its fractional relaxation, (iii)
dropping the location and sequencing constraints, and (iv) replacing
the terminal fleet position by the best-case state value. The
information relaxation is a valid upper bound; each of (ii)–(iv)
further enlarges the feasible set, hence the expectation only
increases.

**Remark (Decomposition of looseness).** The gap `U^R − V*` decomposes
into four components: information gain, integrality loss, sequencing
loss, and terminal optimism. In the v0.3 scenarios the sequencing and
integrality components dominate; the terminal upper bound contributes a
small fraction of total looseness.

The bound is reported with explicit caveats. We do not interpret the
relaxed-bound retention numbers as achievable performance; they
characterize the structural hardness of the problem and bound the
methodological headroom for future work.

### 5.3 Lagrangian-per-truck Information Relaxation

The LP-style relaxation of §5.2 throws away three constraints
simultaneously: per-truck location continuity, per-truck sequencing,
and integrality. Most of its looseness comes from the location-
sequencing relaxation. We tighten the bound by retaining per-truck
structure and dualizing only the cross-truck assignment constraint.

Recall the joint problem `V* = sup_a E[Σ r_t + Φ(F_T)]` subject to
`Σ_k a^(k)_t ≤ 1` for each load `t`. Introduce non-negative duals
`λ = {λ_t ≥ 0}` and form the Lagrangian

`L(λ) = Σ_t λ_t + Σ_k V^k_λ(u^(k)_0)`,

where each per-truck sub-MDP value is

`V^k_λ(u^(k)_0) = sup_{a^(k)} E[Σ_t a^(k)_t (r^(k)_t − λ_t) + ω V(ℓ^(k)_T)]`

with the supremum taken over per-truck policies that respect the
truck's own HOS clocks, pickup-reach time, appointment windows, and
location continuity.

**Proposition 4 (Lagrangian-per-truck upper bound).** For any
`λ ∈ R_{≥0}^{|T|}`, `V* ≤ L(λ)`. Consequently `V* ≤ min_λ L(λ)`, and
the dual minimum is attained at some `λ* ≥ 0` since `L` is convex and
proper in `λ`.

*Proof sketch.* The Lagrangian dualizes only the cross-truck
assignment constraint, with all per-truck constraints retained. For
any `λ ≥ 0`, weak duality gives `V* ≤ L(λ)`. Decomposability of `r_t`
across trucks splits the relaxed supremum into independent per-truck
suprema. Convexity in `λ` follows from the pointwise-supremum-of-
affine characterization.

The dual minimum is attained by subgradient ascent: the subgradient
component on `λ_t` equals `1 − Σ_k a^(k)*_t(λ)`, leading to the update
`λ_t ← max(0, λ_t + α_n (Σ_k a^(k)*_t − 1))` with `α_n = c/√n`.

**Computational construction.** Each per-truck sub-MDP is solved
exactly by forward enumeration of reachable states under common random
numbers (load arrivals and yard delays are deterministic on the
realized scenario). The continuous state space (market, available-
time, drive-used, duty-used) is quantized into buckets at 15-min time
and 1-hour HOS resolutions; on entry to a bucket, clocks are snapped
to the bucket's favorable lower corner. The snapping is permissive
(more time and HOS budget), so per-truck DP values can only over-
estimate the exact per-truck Lagrangian sup, preserving the joint
upper-bound guarantee.

**Convergence and empirical bound.** On the `tight` scenario at eval
seed `20260507` (995 loads, fleet 70), 30 cold-start subgradient
iterations at step scale 100 followed by 20 warm-start iterations from
the iter-30 duals produced the best bound `L* = $1,885,043`. Compared
to the LP-style bound of `$2,377,500`, the Lagrangian bound is **20.7%
tighter**. It remains a valid upper bound: rollout teacher's realized
profit on the same seed is `$1,273,395 < L*`. On the `scarce` scenario
at the same eval seed (1,154 loads, fleet 55), 30 cold-start iterations
at step scale 100 produced `L* = $1,623,084`, **39.3% tighter** than the
LP-style bound of `$2,675,525` and still valid against rollout
(`$1,065,656 < L*`); the bound had stabilized in the
`$1.62`–`$1.63 M` band by iteration 25.

## 6. Policy Classes

The v0.3 policy set comprises simple baselines (`reject_all`,
`accept_all_feasible`, `myopic_margin`, `bid_price`), a dependency-free
linear surrogate (`surrogate_linear`), a finite rollout teacher
(`rollout_teacher`), and a parametric cascade
(`cascade_surrogate_rollout`).

### 6.1 Surrogate

The linear surrogate fits the rollout-label dataset by closed-form
ridge regression on features including load attributes, fleet-state
features, feasibility-probe features (`feasible_accept`,
`service_failure_risk`, `realized_profit_if_feasible`), terminal-value
features (`terminal_origin_value`, `terminal_destination_value`,
`terminal_delta`), and temporal price features
(`price_wave_multiplier`, `price_window_premium`). A surrogate-only
decision additionally consults the feasibility map and rejects if the
copied-fleet probe fails, preventing the surrogate from paying
gratuitous L1 penalties.

**Training protocol.** Features are standardized to zero mean and unit
variance on the training labels (a feature with zero training variance
is left at unit scale), and an explicit, unregularized bias term is
prepended. The regression target is the rollout teacher's incremental
accept-value label, divided by a fixed scale constant. Weights are
obtained in closed form by solving the ridge normal equations
`(X'X + λI) w = X'y` directly, with `λ = 0.25` applied to every weight
except the bias. Labels are generated by the rollout teacher on the
train-seed load streams; all reported surrogate and cascade numbers are
evaluated on disjoint eval seeds, and the held-out label fit is reported
in `freightbidbench_static_label_fit.csv`.

### 6.2 Cascade

Let `π^S_θ` denote the surrogate policy of §6.1 (including its
feasibility guard), let `V_hat_θ(s, a)` denote its score for action `a`
in state `s`, and let `Δ_θ(s) := V_hat_θ(s, 1) − V_hat_θ(s, 0)` be the
signed score margin. The cascade has two escalation triggers. The
*boundary* trigger escalates decisions within a dollar band of the
surrogate's accept/reject boundary; the *scarcity* trigger escalates
decisions for which the origin market has few immediately available
trucks. Concretely, let `o(s)` denote the candidate load's origin
market in state `s` and let

`n_o(s) := |{ k : ℓ^(k)_t = o(s), τ^(k)_t ≤ t }|`

denote the count of trucks in `o(s)` that are immediately available at
the decision time. The cascade policy with boundary band `β ≥ 0` and
scarcity threshold `κ ∈ {−1, 0, 1, 2, …}` (with `κ = −1` disabling the
scarcity trigger) is

`π^{β,κ}_θ(s) = π^R(s)` if `E(s; β, κ) = 1`, else `π^S_θ(s)`,

where the escalation indicator is

`E(s; β, κ) := 1{|Δ_θ(s)| ≤ β} ∨ 1{n_o(s) ≤ κ}`.

Either trigger alone suffices to escalate. The scarcity trigger
intuitively defers the highest-stakes capacity decisions to the
rollout teacher: when the origin market is near-empty, the surrogate's
bias on the disagreement set is most consequential and the value of an
accurate decision is highest. The cascade has three parameters: the
surrogate `θ`, the boundary band `β`, and the scarcity threshold `κ`.
The released configuration freezes `κ = 2` and sweeps
`β ∈ {0, 250, 500, 700, 900}`, with per-scenario best `β` reported
rather than a single global value.

**Proposition 3 (Cascade limit behaviour).** Suppose `Δ_θ(s)` has no
atom at 0 under the stationary state distribution induced by `π^S_θ`
(i.e. `P(Δ_θ(s) = 0) = 0`; `Δ_θ` may otherwise have atoms, as it does
when features are discrete), and let `φ(β, κ) := P(E(s; β, κ) = 1)`
denote the cascade's rollout-call share. Write `κ = −1` for a disabled
scarcity trigger (`1{n_o ≤ κ}` never fires). Then:

(a) With the scarcity trigger disabled and `β = 0`,
`π^{0,−1}_θ = π^S_θ` almost surely: the only escalation set is the
boundary set `{Δ_θ = 0}`, which is null since `Δ_θ` has no atom at 0.
With the scarcity trigger active (`κ ≥ 0`) the cascade escalates
additionally on `{n_o ≤ κ}`; this set need not be null — empty origin
markets occur, notably on `scarce` — so the cascade does *not* reduce
to the pure surrogate at `κ = 0`.
(b) `lim_{β → ∞} π^{β,κ}_θ = π^R` pointwise on the support of `Δ_θ`,
for any `κ ≥ 0`. Similarly, `π^{β,K}_θ = π^R` for `κ = K` at least as
large as the fleet size, regardless of `β`.
(c) `φ(β, κ)` is non-decreasing in `β` (holding `κ` fixed) and in `κ`
(holding `β` fixed); it is right-continuous in `β` and continuous at
every `β` that is not an atom of `|Δ_θ|`.
(d) The expected decision latency
`L(β, κ) = (1 − φ(β, κ)) L_S + φ(β, κ) L_R` is non-decreasing in both
arguments, where `L_S` and `L_R` are the surrogate and rollout
per-decision latencies and `L_R ≥ L_S`.

*Proof sketch.* For (a): with the scarcity trigger disabled the only
escalation set is `{Δ_θ = 0}`, which is null because `Δ_θ` has no atom
at 0; hence the cascade follows `π^S_θ` almost surely. When `κ ≥ 0` the
additional escalation set `{n_o ≤ κ}` carries positive probability in
general, so the reduction fails. For (b): for any state `s`,
there exists `B` such that `|Δ_θ(s)| ≤ B`, hence `β ≥ B` forces
`E = 1`; the second statement follows because `n_o ≤ K` trivially.
Statement (c) follows from the union form of `E` and the fact that
increasing either threshold weakly enlarges the escalation set.
Statement (d) follows from (c) and `L_R ≥ L_S`.

Proposition 3(d) gives the cascade its operational meaning: `(β, κ)`
is a two-knob tradeoff between decision latency and agreement with the
rollout teacher. Fixing `κ = 2` and sweeping `β`, as in the released
configuration, traces a one-dimensional frontier within the larger
`(β, κ)` family.

## 7. Computational Considerations

**State space.** The raw state space is too large for exact enumeration
($|S| = 12$ markets, `K ≤ 90` trucks, discretized continuous time). The
exact small-prefix DP is tractable because the prefix length `L` is
small and the deterministic post-acceptance transition allows
fleet-hash memoization.

**Exact DP scaling.** The exact DP search evaluates up to `2^L`
realizations; with memoization the effective state count is much
smaller. Empirically the search evaluates ~8k states for `L = 12` on
`tight`. We cap `L = 16` in the released configuration.

**Rollout teacher.** Each rollout decision expands accept and reject
branches under common random numbers; mean rollout latency is on the
order of 20–30 ms per decision on the v0.3 scenarios.

**Cascade.** The surrogate handles all decisions in `O(d)` time where
`d` is the feature dimension; only escalated decisions invoke the
rollout teacher. The escalation indicator `E(s; β, κ)` costs `O(1)`
per decision (a count of available trucks in the origin market plus a
single threshold comparison on `|Δ_θ|`). Expected per-decision cost is
`(1 − φ(β, κ)) c_S + φ(β, κ) c_R`.

## 8. Experiments

### 8.1 Setup

All experiments use the v0.3 scenario contract `scenario-v0.3.2`,
default first seed `20260506`, and the public-calibrated lane table at
`data/processed/v1_usda_faf_mapped_lanes.csv`. Reported numbers are
computed from the runs in `benchmark_runs/v03_sweeps/` and assembled
into `benchmark_runs/paper_v03/`. We focus on the `tight` and `scarce`
scenarios; the `mild` scenario remains effectively flat under v0.3 and
is reported as a negative control in the manifest. The headline methods
table reports ten paired (train, eval) seeds; paired-bootstrap 95%
confidence intervals and policy-vs-rollout deltas are computed by
`scripts/analyze_policy_deltas.py` (20,000 resamples).

### 8.2 Layer Ablation

We isolate the contribution of each v0.3 reward layer by holding the
remaining layers at their pre-layer baseline values and varying only the
layer in question. The calibration gate for each layer encodes the
predicted policy-class separation: L1 should push feasibility-blind
policies below the feasibility-aware greedy baseline; L2 should reduce
`accept_all_feasible` retention below 95% of rollout; and L3 should widen
the best-simple retention gap to at least 10 percentage points below
rollout.

**Table 1. Layer marginal effects on the calibration-gate policies
(three-seed full-horizon sweeps). Each row varies one layer with the
other layers held at the pre-layer baseline. "Met" means all policy
comparisons in the gate criterion pass at the listed parameter value.
Sources: `reports/service_failure_penalty_sweep_report.md`,
`reports/terminal_value_sweep_report.md`,
`reports/demand_wave_sweep_report.md`.**

| Layer | Calibration Gate | Tight | Scarce |
| --- | --- | --- | --- |
| L1 (`ρ ∈ {0, 10}`)              | `myopic`, `bid_price` < `accept_all_feasible` | met at `ρ=10` (gap −$3.1k) | met at `ρ=10` (gap −$3.7k) |
| L2 (`ω ∈ {0, 0.25}`, L1 on)     | `accept_all_feasible` retention ≤ 95% | met at `ω=0.25` (89.7%) | met at `ω=0.25` (93.9%) |
| L3 (amp `∈ {0, 0.5}`, L1+L2 on) | best-simple retention gap ≥ 10 pp | met at amp `=0.5` (11.1 pp) | met at amp `=0.5` (14.5 pp) |

Three patterns confirm Proposition 1 and the qualitative role of L2 and
L3.

- **L1 separates feasibility-blind policies.** Under `ρ = $10`,
  `myopic_margin` and `bid_price` fall strictly below
  `accept_all_feasible` on both scenarios. The realized gap (−$3.1k
  tight, −$3.7k scarce) matches the infeasible-accept counts multiplied
  by `ρ`, in agreement with Proposition 1.
- **L2 demotes `accept_all_feasible`.** Terminal value weight `ω = 0.25`
  alone reduces `accept_all_feasible` retention to 89.7% on tight and
  93.9% on scarce. L2 acts on the feasibility-aware greedy policy
  exactly because that policy is otherwise insensitive to terminal
  fleet positioning.
- **L3 widens the rollout gap.** The price-premium window at amplitude
  `0.5` widens the rollout-versus-best-simple gap to 11.1 pp on tight
  and 14.5 pp on scarce, providing the residual headroom that the
  cascade results in §8.3 exploit.

### 8.3 Methods Frontier

**Table 2. Ten-seed methods comparison under `scenario-v0.3.2`.
Retention is mean closed-loop profit relative to the rollout teacher;
the cascade row uses the representative escalation band `β = $500` at
frozen scarcity threshold `κ = 2`. The final column is the
paired-bootstrap 95% CI on the cascade-minus-rollout profit delta
(`n = 10`, 20,000 resamples); an interval containing $0 means the
cascade is statistically indistinguishable from rollout.**

| Scenario | Best Simple | Surrogate | Cascade (β=$500) | Cascade ms | Rollout ms | Cascade−Rollout Δ (95% CI) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `tight`  | 91.0% | 94.2% | 98.2% | 12.95 | 32.11 | −$23.3k [−$61.2k, +$11.6k] |
| `scarce` | 86.5% | 89.3% | 98.0% | 11.54 | 20.59 | −$20.7k [−$33.4k, −$7.2k] |
| `mild`   | 100.1% | 98.2% | 99.7% |  8.31 | 49.50 | −$4.2k [−$18.2k, +$11.0k] |

**Table 2b. Cascade latency–profit frontier over the boundary band
`β ∈ {0, 250, 500, 700, 900}` at `κ = 2`. Rollout share is the fraction
of decisions escalated to the rollout teacher.**

| Scenario | β | Retention | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: |
| `tight`  |   0 | 97.7% |  6.27 | 28.6% |
| `tight`  | 500 | 98.2% | 12.95 | 44.7% |
| `tight`  | 900 | 99.0% | 17.72 | 57.0% |
| `scarce` |   0 | 93.7% |  6.09 | 45.4% |
| `scarce` | 500 | 98.0% | 11.54 | 59.6% |
| `scarce` | 900 | 99.5% | 15.72 | 78.6% |

Three interpretive points. First, the cascade is the only stdlib policy
that closes the gap to rollout: at `β = $500` it recovers ~98% of
rollout profit on both stress scenarios at 40% (`tight`) to 56%
(`scarce`) of rollout's mean decision latency. On `tight` the paired
cascade-minus-rollout difference is not statistically significant (the
95% CI spans zero), so the cascade matches the rollout teacher to within
sampling error while escalating fewer than half of all decisions; on
`scarce` a small but significant ~2% gap remains. Second, the frontier
is smooth and monotone in `β` (Table 2b), consistent with Proposition
3(d): larger bands escalate more decisions, trading latency for
retention, and the scarcity trigger alone (`β = $0`) already recovers
97.7% on `tight` but only 93.7% on `scarce`, where the surrogate's
disagreement set with rollout extends well beyond the scarcity regime.
Third, the standalone surrogate clears the best-simple bar on both
scenarios (94.2% vs 91.0% on `tight`; 89.3% vs 86.5% on `scarce`), but
it still leaves
roughly 6–11 points of rollout value on the table, all of which the
cascade recovers. The surrogate is a competent ranker but a poor
substitute for selective lookahead on the high-stakes decisions, which
is precisely what the scarcity and boundary triggers escalate.

### 8.4 Hindsight Diagnostics

**Table 3. Exact small-prefix hindsight diagnostic.**

| Scenario | Loads | Hindsight | States | Best Simple | Simple Retention | Rollout Retention |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| `tight` | 12 | $53,419 | 8,191 | `accept_all_feasible` | 100.0% | 90.0% |

**Table 4. Full-horizon upper bounds and rollout-teacher retention
against each ceiling. The Lagrangian-per-truck bound retains per-truck
structure and is 20.7% tighter than the LP relaxation on `tight` and
39.3% tighter on `scarce`. Rollout retention against the ceiling rises
from 53.6%/39.8% (LP) to 67.6%/65.7% (Lagrangian).**

| Scenario | Loads | LP-style Bound | Rollout ret. (LP) | Lagrangian Bound | Rollout ret. (Lag) | Tightening |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `tight`  |   995 | $2,377,500 | 53.6% | $1,885,043 | 67.6% | 20.7% |
| `scarce` | 1,154 | $2,675,525 | 39.8% | $1,623,084 | 65.7% | 39.3% |

The looseness reduction is structural rather than numerical: the
Lagrangian relaxation keeps per-truck location continuity, sequencing,
and HOS budgets while dualizing only the cross-truck assignment. This
matches the looseness decomposition in §5.2 — sequencing and
integrality dominated the LP's slack, and the Lagrangian recovers most
of that lost tightness. Rollout retention against the Lagrangian bound
jumps from 53.6% to 67.6% on `tight` and from 39.8% to 65.7% on
`scarce` — the larger tightening on `scarce` (39.3%) reflects that the
loose LP bound was most optimistic exactly where capacity is most
binding. In both cases the Lagrangian ceiling locates the v0.3 rollout
teacher much closer to the dependency-free upper bound and characterizes
methodological headroom more honestly.

### 8.5 Sensitivity Analysis

**Table 5. Sensitivity of the qualitative ordering to v0.3 parameter
choices. Each row reports whether the calibration gate
(myopic/bid_price below `accept_all_feasible` for L1;
`accept_all_feasible` retention ≤ 95% for L2; best simple retention
≤ 90% for L3) is met.**

| Parameter | Tested Values | Frozen Value | Gate Met (tight) | Gate Met (scarce) |
| --- | --- | --- | --- | --- |
| `ρ` (L1, $)   | {0, 10, 25, 50}       | 10  | {no, yes, yes, yes} | {no, yes, yes, yes} |
| `ω` (L2)      | {0, 0.1, 0.25, 0.5, 1.0} | 0.25 | {no, no, yes, yes, yes} | {no, no, yes, yes, yes} |
| L3 amplitude  | {0, 0.25, 0.5, 0.75}  | 0.5 | {no, no, yes, yes}   | {no, yes, yes, yes} |

## 9. Discussion and Managerial Insights

**Operational feasibility is a reward, not a side diagnostic.**
Proposition 1 formalizes a simple operational truth: any policy that
ranks tenders without checking feasibility will pay a linear
service-failure tax on its infeasible-accept rate. In a production
context, scoring systems that surface tenders to dispatchers without
upstream feasibility checks therefore have a hidden expected cost that
scales with the operational mismatch rate. The L1 calibration in v0.3
suggests this cost can be substantial even with a modest per-event
penalty.

**Cascade structure is the right framing, not standalone surrogate.**
The v0.3 surrogate is biased on the disagreement set with the rollout
teacher in the `scarce` regime, where capacity-positioning is most
consequential. The cascade recovers nearly all of rollout's profit by
escalating exactly these uncertain decisions. The implication for
practice is that a cheap learned model deployed as a sole policy will
under-perform in the regimes where future-aware decisions matter most;
the value of the model comes from selectively deferring uncertain
decisions to a more expensive teacher.

**Methodological headroom is smaller than the LP relaxation suggests,
once per-truck structure is respected.** The LP-style bound loses most
of its tightness to dropping sequencing, location, and integrality
constraints simultaneously; the Lagrangian-per-truck information
relaxation (Proposition 4) retains those constraints and tightens the
bound by 20.7% on `tight`. Rollout retention against the Lagrangian
bound rises from 53.6% to 67.6%, characterizing the achievable
methodological headroom more honestly. The remaining gap to the
Lagrangian bound is dominated by the residual cross-truck-assignment
dual slack: the headroom for future methods work lies in tighter
inter-truck coordination (joint-decision lookahead, dual-price-aware
features in the surrogate, or anytime joint optimization), not in
further refinement of single-tender scoring.

## 10. Limitations

FreightBidBench remains synthetic and public-calibrated, not a private
tender dataset; the calibration is validated against its FAF/USDA
sources in Appendix B, which also documents that the v1 USDA-reefer lane
subset concentrates load draws on a few high-volume Texas and Georgia
origins. The HOS model is simplified to property-carrying
11/14/10 clocks and omits split-sleeper, recap, home-time, and
team-driver rules. The rollout teacher is a finite-lookahead stochastic
benchmark, not a true oracle: a cheaper policy can exceed 100%
retention on a given seed. The exact hindsight DP is tractable only for
small load prefixes. The relaxed full-horizon bound is intentionally
loose; it characterizes problem hardness rather than achievable profit.
The dependency-free methods track means that stronger learned baselines
are outside scope for v0.3 and should not be required for
reproducibility tests.

## 11. Conclusion

FreightBidBench v0.3 turns the v0.2 feasibility calibration into a
sharper, reproducible benchmark for online truckload bid acceptance.
The three new reward components each separate a distinct policy class;
the two-tier hindsight ceilings provide both a trustworthy
small-instance reference and a structurally honest full-horizon upper
bound; and the parametric surrogate-rollout cascade admits a clean
limit characterization and demonstrates a non-trivial latency-profit
frontier on the benchmark. The benchmark itself is the primary
artifact: future methods work — stronger surrogates, joint-decision
lookahead, learned cascade-band selection — can be evaluated against
the released ceilings and the versioned scenario contract without
ambiguity over what exactly is being compared.

## Declaration of Competing Interest

The author is employed by Bubba AI, which develops AI-based load-planning
and carrier-operations products in the freight domain addressed by this
paper. This study uses only public Freight Analysis Framework and USDA data
and a dependency-free, open-source benchmark; no proprietary data or
systems were used, and Bubba AI had no role in the study design, the
analysis, or the decision to publish. The author declares no other
competing interests.

## Appendix A. Reproducibility

**Software.** Python 3.10 or newer, standard library only at runtime.
No third-party dependencies are required to reproduce any table in
this paper.

**Hardware.** Reported single-threaded latencies were measured on a
2024-class laptop (Apple silicon). Closed-loop simulator runtime is
dominated by Python interpreter overhead; absolute latencies are
reference latencies and not optimized serving latencies.

**Versioning.** The release pins three version strings in
`configs/freightbidbench_v03_scenarios.json`: benchmark version
`freightbidbench-v0.3`, scenario configuration version
`scenario-v0.3.2`, and policy set version `policy-set-v0.3.0`. The
default first seed is `20260506`.

**Manifest schema.** Every run writes a `freightbidbench_manifest.json`
containing the command line, the three version strings, the seed pairs
evaluated, the source input paths, the feasibility configuration, the
scenarios, the output paths, and the row counts for each output CSV.
The manifest is the canonical reproducibility anchor.

**Headline run commands.**

```bash
python3 scripts/run_freightbidbench.py \
  --config configs/freightbidbench_v03_scenarios.json \
  --preset standard --scenarios tight,scarce \
  --seed-count 3 --label-limit 200 \
  --cascade-bands 0,250,500,700,900 \
  --output-dir benchmark_runs/v03_sweeps/methods_cascade_seed3_label200

python3 scripts/run_relaxed_hindsight_bound.py \
  --config configs/freightbidbench_v03_scenarios.json \
  --scenario tight \
  --policies accept_all_feasible,bid_price,rollout_teacher \
  --output-dir benchmark_runs/v03_sweeps/relaxed_bound_tight_full_rollout

make hindsight-smoke
make paper-v03-tables
```

**Layer-ablation source.** Values in Table 1 are assembled from the
calibration sweeps under
`benchmark_runs/v03_sweeps/service_failure_penalty/`,
`benchmark_runs/v03_sweeps/terminal_value/`, and
`benchmark_runs/v03_sweeps/demand_waves_price_selected_seed3/` as
documented in `reports/service_failure_penalty_sweep_report.md`,
`reports/terminal_value_sweep_report.md`, and
`reports/demand_wave_sweep_report.md`.

## Appendix B. Calibration Validation

The "public-calibrated" claim is not merely nominal: the simulator's
load, fleet, distance, price, and terminal-value primitives are all
derived from public Freight Analysis Framework (FAF 5.7.1, 2024 truck
mode) and USDA Agricultural Marketing Service (AMS Specialty Crops
Market News, `fvwtrk` truck-rate) data through the pipeline in
`scripts/inspect_public_sources.py`. Concretely: candidate loads are
drawn with probability proportional to lane `faf_tons_2024`; the initial
fleet is placed proportional to per-origin FAF outbound tonnage; lane
distance is `1000 · faf_tmiles_2024 / faf_tons_2024`; posted prices are
drawn from each lane's USDA AMS rate band `[rate_low, rate_high]`; and
the terminal state-value signal `V(·)` of §3.3 is computed from FAF
outbound intensity and the FAF/USDA net-outbound imbalance panel. The
cross-checks below are reproduced by `scripts/analyze_calibration.py`
(dependency-free), which writes `reports/calibration_report.md`.

**B.1 Origin intensity vs FAF outbound flow.** Because load draws and
fleet placement are FAF-tonnage-weighted, each origin's load-draw share
equals its share of total lane FAF tonnage; the FAF outbound and
net-outbound tons are the independent cross-check from the state
imbalance panel.

| Origin state | Load-draw share | FAF outbound tons 2024 | Net outbound tons 2024 |
| --- | ---: | ---: | ---: |
| Texas      | 78.8% | 1,517,190 | +19,720 |
| Georgia    | 16.3% |   348,979 |  −7,477 |
| California |  3.9% |   756,331 |  −1,448 |
| Arizona    |  0.6% |   134,239 |  −3,447 |
| Washington |  0.4% |   265,827 |  −8,130 |
| Colorado   |  0.1% |   157,922 |  −2,894 |

**B.2 Haul-length distribution.** Lane distances span 88–3,081 mi
(median 2,211; IQR 1,454–2,770), but the tonnage-weighted mean is only
208 mi: FAF truck tonnage concentrates on short intra-state metro flows.
A single lane, Texas→Dallas, accounts for 77.2% of tonnage at 105 mi,
and Georgia→Atlanta for 15.0% at 88 mi. The realized closed-loop load
mix is therefore short-haul-dominated with a long interstate tail — a
faithful reflection of FAF truck flow on this lane subset, and a scope
limitation discussed below.

**B.3 Price calibration vs USDA AMS.** Posted prices come from the USDA
AMS rate bands (73 of 74 lanes have a positive-width band). The implied
per-mile rate has median $3.28 and IQR $2.83–$3.57, consistent with
published refrigerated truckload spot rates; the single high outlier is
a short, distance-clamped lane.

**Scope of the v1 lane set.** The USDA-reefer-mapped lane catalog is
concentrated on a few high-volume Texas and Georgia origins. This is
correct FAF behavior for the mapped subset, but it means the benchmark's
closed-loop dynamics are driven substantially by short-haul
intra-state repositioning. Broadening lane coverage beyond the USDA
reefer subset — to the full FAF truck OD matrix — is a calibration
extension for a future release; operational-metric calibration against
ATRI/FMCSA carrier benchmarks is likewise deferred.
