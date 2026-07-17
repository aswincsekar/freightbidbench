# Path C Workplan: Certified-Gap Dual-Price Policies for Truckload Bid Acceptance

## Groundwork Results (2026-07-12 → 07-15)

**DP-1: PASSED.** The value-function dual policy (`dual_price_vf`: probe
profit − λ̂(origin, hour) + same-time spatial gradient
W(dest,t)−W(origin,t)) reaches 95.1% (tight) / 90.8% (scarce) mean
retention vs rollout on 9 held-out pairs — beats/ties the rollout-trained
surrogate with ZERO training labels at ~0.02–0.07 ms. Key design lesson:
subtracting W(origin, now) double-counts the busy-time cost that λ prices
(collapsed to 14% retention); the same-time spatial gradient is the correct
decomposition and should be formalized in Theorem A. Prices are PORTABLE
(frozen one-stream duals ≡ fresh train-stream duals, identical decisions),
and policy-grade duals need only ~15 subgradient iters (~3× cheaper than
bound-grade).

**Theorem B groundwork (fleet scaling, proportional K + arrivals, tight):**

| cell | K | bound | V(policy) | certified | gap | vs rollout | bound/K | V/K |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| x05 | 35 | $937,290 | $603,456 | 64.4% | 35.6% | 116.6% | 26,780 | 17,242 |
| x1 | 70 | $1,885,043 | $1,187,928 | 63.0% | 37.0% | 93.3% | 26,929 | 16,970 |
| x2 | 140 | $4,421,848 | $2,114,588 | 47.8% | 52.2% | 96.9% | 31,585 | 15,104 |

Policy is scale-robust vs rollout (96.9% at 2×; rollout latency grows 32→159
ms while policy stays ~0.1 ms — the speed advantage WIDENS with scale). The
certified gap grows at x2 from BOTH sides: bound/K inflates +17% (dual slack:
avg λ still climbing at iter 45, only 22 loads priced as overused among
2,035) and V/K dips −11% (rollout dips similarly). Open question: is the x2
bound slack structural or under-optimized duals (diminishing step too small
at scale)? Discriminating test: fresh x2 solve with scale-aware step_scale.
Theorem B framing should be: policy consistency in the fluid limit +
certificates require solver effort scaling with K (characterize the
schedule), not raw gap→0 at fixed effort.

**Infra:** long runs go on the Hetzner VM (ops@178.105.83.153,
~/freightbidbench). `run_lagrangian_bound.py` now has `--workers N`
(stdlib multiprocessing over per-truck sub-MDPs, bit-identical to serial;
measured 3.05× on 4 shared vCPUs) and per-iteration dual checkpoints
(`lagrangian_duals_checkpoint.csv`) for resume after interruption.

Date: 2026-07-08. Status: planning. This is the methods-paper track that
follows the v0.3 benchmark release (arXiv submitted; CompOR submission in
flight). It supersedes the Path B TransSci ambitions with a sharper,
lit-review-validated positioning, and will drive the v0.4 benchmark release.

## 1. Objective and headline claim

**Working title:** *Certified-Gap Dual-Price Policies for Real-Time
Truckload Bid Acceptance with Relocating, Clock-Constrained Resources.*

**Primary venue:** Transportation Science. Fallbacks: Operations Research
(if Theorem B lands strongly), TR-B/TR-E (if theory retreats to
fluid/empirical). The paper claims, in order:

1. **Model.** A weakly coupled DP for online load acceptance in which the
   resources (trucks) are *relocating and clock-constrained*: serving a
   request executes a controlled state transition of the resource (new
   market, depleted HOS clocks), and request–resource feasibility depends
   on the resource's internal state. This distinguishes the model from the
   reusable-resources online-allocation literature, where units return to
   an unchanged pool and feasibility is availability-only.
2. **Policy + certificate.** A real-time dual-price acceptance policy
   derived from the per-truck Lagrangian value functions, paired with the
   Lagrangian upper bound computed from the *same* dual object, yielding a
   per-instance certified optimality gap. The mechanism is the standard
   weakly-coupled playbook (Hawkins 2003; Adelman & Mersereau 2008;
   Topaloglu 2009) — the contribution is its extension to relocating,
   state-dependent-feasibility resources and its instantiation at
   sub-millisecond decision latency.
3. **Online variant.** A training-free dual-update policy (mirror-descent
   style) that learns prices during the horizon itself, analyzed under the
   benchmark's periodic (L3) arrival non-stationarity. Positioned as a
   structural extension of Balseiro–Lu–Mirrokni-type analysis to
   state-transitioning resources — NOT as a regret-rate improvement
   (O(√T) is commodity; the frontier is O(log)/O(1) in plain settings).
4. **Compute-aware deferral (secondary).** A learned escalation rule from
   the dual-price policy to Monte Carlo rollout, with the deferral-regret
   identity and a value-of-computation decision rule — the first such
   treatment in an OR/freight setting (MCTS-VOC work is toy-domain only).
5. **Evaluation on the public benchmark** (FreightBidBench v0.4), with
   30-seed paired-bootstrap statistics, certified gaps per scenario, and a
   latency–profit frontier extended by a new sub-millisecond extreme point.

## 2. Positioning discipline (from the 2026-07-08 lit review)

- Do NOT claim novelty for: bid-price control from dual approximations
  (Adelman 2007), the policy+bound certified-gap mechanism (standard since
  Hawkins/Adelman–Mersereau; Topaloglu 2009 reports both on the same NRM
  instances), dual prices for truckload fleet state (Simão et al. 2009
  marginal values), or O(√T) dual-descent regret (Balseiro et al. 2020).
- Cite as the immediate theory backdrop and differentiate structurally:
  Zhang–Cheung (arXiv:2212.02855; homogeneous reusable units), *Online
  Allocation of Reusable Resources in Nonstationary Environments* (Math of
  OR, moor.2023.0250; dual learning + minimax regret, but units return
  unchanged), fluid-guided reusable allocation, and ride-hailing
  dispatch/repositioning (adjacent lane; different framing — no
  certificates).
- The defensible novelty sentence: *"resources whose service capability is
  itself a controlled state variable"* — relocation + HOS clocks + windows.
  Every claim in the paper should survive deletion of anything not covered
  by that sentence.
- **Scoop watch:** re-run a targeted search monthly (reusable resources +
  relocation/state; online freight acceptance duals; MOOR/Cheung/Balseiro
  author feeds). Early-arXiv the theory core as soon as Theorems A+B are
  drafted, before the full empirical program completes.

## 3. Theory program

Let `x_k ∈ X` be truck k's state (market, next-free time, drive/duty
clocks), `ξ_t` the tendered load, and `f(x_k, ξ_t)` the feasibility map.
Serving moves the truck: `x_k ← T(x_k, ξ_t)` (new market, advanced clocks).
The joint DP couples trucks only through the one-truck-per-load constraint.

**Theorem A — Certified gap for relocating resources (medium risk).**
Define the dual-price policy `π_λ`: on tender `ξ_t`, accept with truck
`k* = argmax_k [r(x_k, ξ_t) − λ_t + V^k_λ(T(x_k, ξ_t)) − V^k_λ(x_k)]`
if the argmax value is ≥ 0 and `f(x_k*, ξ_t)` holds; else reject. Prove:
(i) validity of the per-instance certificate
`gap(ξ) = L(λ; ξ) − V^{π_λ}(ξ) ≥ L(λ; ξ) − V*(ξ) ≥ 0` (assembly from
weak duality — the content is the construction and its state-dependent
form); (ii) a bound on `E[gap]` in terms of expected complementary-
slackness violation / dual over-use, in the spirit of Brown–Zhang (2023)
relaxation-gap analysis, adapted to state-dependent linking constraints.
*Exit criterion:* both parts written and internally reviewed; (ii) may
weaken to structural characterization + measured decomposition if a clean
bound resists.

**Theorem B — Asymptotic optimality in the large-fleet regime (high risk;
the differentiator).** Scale fleet size K and arrival rate together; prove
`V^{π_λ*} / V* → 1` under fleet-mixing conditions (every market reachable,
clocks renew via rests, bounded occupancy). This is the Talluri–van Ryzin /
Levi–Radovanović style result, which exists for static and plain-reusable
resources but (per the scoop check) not for relocating, clock-constrained
ones. *Fallback if stuck at week 8:* prove it for a relaxed model (no
clocks, relocation only), state the clocked case as a conjecture with
strong empirical support; venue expectation drops one notch.

**Theorem C — Online dual updates under periodic non-stationarity (medium
risk).** Per-decision multiplicative/mirror update of market-time bucket
prices with no training phase. Target: sublinear regret vs the offline
dual benchmark under known-period arrival modulation, with the relocation
dynamics handled via a drift/mixing argument. Honest framing: structural
extension; if the MOOR machinery adapts trivially, demote to a proposition;
if it breaks, that break IS the contribution — document exactly where.
*Fallback:* empirical dual-convergence + regret curves, theorem deferred.

**Proposition D — Deferral regret identity + VOC rule (low risk).** Recycle
Path B's Theorem 2 with the dual-price policy as the cheap stage: escalate
to rollout iff estimated value-of-computation (predicted disagreement ×
predicted regret) exceeds the latency price. First compute-aware deferral
result instantiated in freight OR.

## 4. Implementation program

All dependency-free (stdlib), consistent with the benchmark contract.

1. **Dual extraction + λ̂ fitting** (`scripts/fit_dual_prices.py`): from
   converged `lagrangian_dual_prices.csv` across train seeds, fit
   `λ̂(market, hour-of-day)` tables (granularity ablation: global constant /
   per-market / per-market-hour). Reuses existing solver outputs.
2. **Per-truck value tables** (`scripts/run_lagrangian_bound.py` extension):
   emit `V^k_λ(x)` on the bucketed state grid (already computed internally
   during forward enumeration — add an export flag).
3. **Dual-price policy** (new branch in `choose_action()`,
   `scripts/run_surrogate_cascade.py`, policy name `dual_price`): O(#trucks
   in origin market) lookups per decision; target latency ≪ 1 ms. Must not
   mutate load/fleet, per the policy contract.
4. **Online variant** (policy name `dual_price_online`): starts from λ = 0
   (or λ̂ prior), updates bucket prices after each decision; no training
   seeds consumed — report as the "cold-start" row.
5. **Certified-gap reporting** (`scripts/report_certified_gaps.py`): per
   scenario × seed, compute `L(λ*; ξ)` (existing bound runs, warm-started)
   and `V^π(ξ)` for every policy; output gap tables for the paper.
6. **Deferral** (`scripts/run_deferral_cascade.py`): log
   (state, dual-policy action, rollout action, margin, n_o) on train seeds;
   fit stdlib logistic disagreement model; cascade = dual_price + learned
   escalation; compare against the v0.3 threshold cascade.
7. **Contract/version bump:** new policies enter `policies.default` →
   `policy-set-v0.4.0`, `freightbidbench-v0.4`; regenerate golden smoke
   fixture in the same commit; `make smoke` + tests green.

## 5. Empirical program

- **Headline table:** 30 paired seeds × {mild, tight, scarce} × policies
  {best-simple, surrogate, threshold cascade, rollout, dual_price,
  dual_price_online, dual+VOC cascade}, paired-bootstrap CI95 + sign tests
  (Path B §6.6 statistical protocol applies).
- **Certified-gap table:** mean and per-seed `gap/L*` for each policy —
  the paper's signature exhibit ("policy X is provably within Y% of
  optimal on this instance").
- **Latency frontier:** extended with the sub-millisecond dual-price point;
  report where the dual policy sits vs the v0.3 cascade (expectation: less
  profit than cascade, dramatically less latency; the dual+VOC cascade
  should dominate the v0.3 threshold cascade).
- **Ablations:** λ̂ granularity; warm vs cold duals; L3 window on/off
  (non-stationarity stress for Theorem C's empirics); fleet-size scaling
  K ∈ {25, 55, 90, 180} for Theorem B's asymptotic story.
- **Stretch (answers the v0.3 concentration critique):** a broadened-lane
  scenario from the full FAF truck OD matrix as a v0.4 scenario; decide at
  DP-2 whether it enters this paper or waits.

## 6. Decision points

- **DP-1 (end week 4): does the dual-price policy work empirically?** Gate:
  `dual_price` ≥ standalone surrogate retention on tight and scarce at
  ≤ 1 ms latency. If it fails, the paper premise is broken — investigate
  (λ̂ granularity, terminal-value interaction) before any theory investment.
- **DP-2 (end week 8): Theorem B viability.** Clean large-fleet proof on
  track → hold Transportation Science/OR ambition. Only the relaxed
  (no-clock) version provable → TransSci with conjecture + empirics, or
  TR-B. Neither → reposition as certified-gap empirical methods paper at
  TR-E; still publishable, decide deliberately.
- **DP-3 (end week 10): early-arXiv the theory core** (model + Theorems
  A/B + preliminary gaps) regardless of empirical completeness — scoop
  insurance for the fast-moving reusable-resources lane.

## 7. Risks

| Risk | P | Mitigation |
| --- | --- | --- |
| Dual policy empirically weak vs cascade | med | It only needs to beat the surrogate as the cheap stage; the dual+VOC cascade is the headline policy |
| Theorem B intractable with clocks | med-high | Relaxed-model proof + conjecture; empirics at scaling K |
| Scooped on relocating-resource online duals | med, rising | Monthly scoop watch; DP-3 early arXiv |
| Reviewer: "ride-hailing did this" | med | Explicit positioning section: certificates + feasibility clocks + accept/reject (not matching/pricing) |
| Certified gaps unimpressive (large) | low-med | Gap decomposition (dual slack vs policy loss); tighten λ̂; honest reporting — a 30% certified gap is still a certificate nobody else provides |
| Solo-author bandwidth | high | Sequence strictly: implementation (weeks 1–4) → theory (4–10) → 30-seed program (8–12) → writing (10–16) |

## 8. Out of scope (each is its own paper)

Neural surrogates or learned λ̂ beyond stdlib; multi-leg/continuous-move
planning; dynamic pricing; real tender data; regret-rate records in plain
online-LP settings; benchmark leaderboard infrastructure.

## 9. Effort estimate

Implementation 3–4 weeks; theory 5–7 weeks (overlapping); 30-seed compute
~2–3 days wall-clock (parallelizable by seed); writing 4–5 weeks. **~4
months to submission**, early-arXiv of the theory core at ~week 10.
Competing-interest disclosure (Bubba AI) and AI-use acknowledgment carry
over verbatim from the v0.3 paper.
