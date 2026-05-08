# FreightBidBench: A Public-Calibrated Benchmark for Real-Time Truckload Bid Acceptance Under Operational Feasibility Constraints

## Abstract

Truckload carriers and brokers must make accept/reject decisions under tight
latency constraints, uncertain future demand, and operational feasibility
constraints. Existing academic formulations often study dynamic fleet management
or stochastic vehicle routing, but reproducible public benchmarks for real-time
truckload bid evaluation remain limited. We introduce FreightBidBench, a
public-calibrated synthetic benchmark built from FAF freight-flow structure and
USDA AMS truck-rate reports. FreightBidBench evaluates policies in closed loop:
accepted loads move trucks through the network, consume driver availability, and
affect future opportunity cost. Version 0.2 adds individual truck state, pickup
reach time, pickup and delivery windows, simplified hours-of-service clocks, and
stochastic shipper/receiver yard delays. The benchmark reports profit,
latency, rollout-call share, infeasible accept attempts, HOS rest hours,
deadhead miles, yard-delay hours, and profit retention relative to a finite
rollout teacher. We provide a dependency-free reference runner, manifest format,
baseline policies, and latency-profit frontier outputs. A standard-preset
ablation study shows that appointment windows and HOS constraints are
first-order benchmark features, not minor bookkeeping.

## 1. Introduction

Real-time truckload bid acceptance is a high-pressure sequential decision
problem. A carrier can accept a load that looks profitable immediately but sends
a truck into a weak future market, violates pickup feasibility, or consumes
driver hours needed for a better future load. Conversely, rejecting a low-margin
load can be costly when the destination improves fleet positioning.

The main obstacle to reproducible research in this setting is not only model
choice. It is the lack of a public benchmark that combines stochastic demand,
closed-loop fleet state, bid-evaluation latency, and operational feasibility.
Private tender data is rarely shareable. Production dispatch systems are
complex and unavailable to most researchers.

FreightBidBench addresses this gap with a public-calibrated benchmark rather
than a claim of production-grade simulation. The purpose is to create a common
testbed where researchers can compare policies on the same stochastic freight
environment and report the same latency-profit metrics.

## 2. Contributions

1. We introduce FreightBidBench, a reproducible public-calibrated benchmark for
   real-time truckload bid acceptance.
2. We define a closed-loop synthetic freight environment calibrated from public
   FAF and USDA-derived inputs.
3. We add a v0.2 operational feasibility layer with individual trucks, pickup
   reach time, pickup/delivery appointment windows, simplified HOS clocks, and
   stochastic yard delays.
4. We provide reference policies: reject-all and accept-all-feasible sanity
   baselines, myopic margin, bid-price heuristic, linear rollout-label
   surrogate, selective surrogate/rollout cascade, and finite rollout teacher.
5. We define benchmark reporting rules: seed protocol, manifest, latency-profit
   frontier, feasibility metrics, and confidence intervals.
6. We provide feasibility ablations showing that removing appointment windows or
   HOS can more than double fast-policy profit in tight and scarce scenarios.

## 3. Related Work

FreightBidBench sits at the intersection of dynamic freight acceptance,
stochastic vehicle routing, approximate dynamic programming, learning-augmented
optimization, and public freight data.

**Dynamic truckload acceptance and fleet management.** Dynamic truckload routing
and load acceptance has long been recognized as an online, state-dependent
decision problem. Kim, Mahmassani, and Jaillet study dynamic load acceptance and
rejection decisions for large-fleet truckload operations with time windows and
priority demand [@kim2004dynamic]. Simão et al. show how approximate dynamic
programming can estimate marginal driver values in large-scale truckload fleet
management [@simao2009adp]. FreightBidBench builds on this tradition but changes
the artifact: instead of proposing one dispatch method, it provides a benchmark
where future-value policies, rollout teachers, and fast approximations can be
compared under the same stochastic seeds and latency measurements.

**Dynamic and stochastic vehicle routing.** Surveys by Pillac et al. and
Ritzinger et al. describe the broader dynamic and stochastic vehicle-routing
literature, including the role of information evolution and the distinction
between online computation and offline policy construction
[@pillac2013review; @ritzinger2016survey]. Ulmer et al. combine offline value
function approximation with online rollout for dynamic routing with stochastic
requests [@ulmer2019offline], while Ulmer and Thomas study value-function
approximations for dynamic customer acceptance in delivery routing
[@ulmer2020meso]. These papers motivate FreightBidBench's finite rollout teacher
and surrogate baselines. The benchmark gap is that truckload bid evaluation also
requires public calibration, fleet repositioning, operational feasibility, and
latency-profit reporting.

**Learning-augmented optimization.** Recent work uses learned models to speed
up routing and stochastic optimization. Nazari et al. and Kool et al. show that
neural policies can learn routing heuristics with fast inference after training
[@nazari2018rlvrp; @kool2019attention]. Patel et al. approximate expensive
two-stage stochastic-programming value functions with neural surrogates
[@patel2022neur2sp]. Derrow-Pinion et al. demonstrate graph neural networks for
large-scale transportation ETA prediction [@derrowpinion2021eta]. These works
support future FreightBidBench submissions, but the benchmark contribution is
not a neural architecture. It is a reproducible environment and reporting
protocol for closed-loop truckload bid evaluation.

**Public freight data and feasibility rules.** FreightBidBench uses the Freight
Analysis Framework as a public freight-flow backbone [@btsfaf5] and USDA AMS
Specialty Crops National Truck Rate Reports for refrigerated truck-rate and
availability signals [@usdafvwtrk]. The v0.2 feasibility layer uses a simplified
property-carrying HOS abstraction based on FMCSA's 11-hour driving limit,
14-hour driving window, and 10-hour off-duty reset summary [@fmcsa_hos]. These
data sources make the benchmark reproducible while also defining its limits:
the generated tenders are synthetic and public-calibrated, not private carrier
histories.

## 4. Benchmark Design

### 4.1 Decision Problem

At each decision epoch, the environment tenders a candidate load. A policy
chooses:

```text
accept or reject
```

If accepted, the benchmark attempts to assign a feasible truck. If no feasible
truck exists, the accepted load creates a no-truck or infeasible outcome. If
feasible, the truck moves to the destination and becomes available after
pickup, linehaul, delivery, yard delays, and required HOS rest.

### 4.2 State

The v0.2 state includes:

- candidate load origin/destination,
- load price and direct cost,
- lane distance and public-calibrated intensity,
- state-level future-value features,
- individual truck location and availability time,
- simplified HOS drive/duty clocks,
- pickup and delivery appointment windows,
- pickup deadhead time,
- stochastic yard-delay realizations.

### 4.3 Reward

For accepted feasible loads:

```text
profit = price
       - direct linehaul cost
       - pickup deadhead cost
       - pickup/dropoff yard-delay cost
```

Rejected loads receive zero immediate reward and preserve fleet state.

## 5. Public Calibration

FreightBidBench uses:

- FAF state-level freight flows to seed origin-destination intensity and
  regional imbalance,
- USDA AMS FVWTRK truck-rate reports to seed refrigerated truckload rates and
  availability categories.

The benchmark does not claim that generated loads are production tenders.
Instead, public data anchors broad flow, rate, and scarcity structure so the
benchmark is reproducible and inspectable.

**Table 1. Public calibration inputs used in FreightBidBench v0.2.**

| Source | Benchmark Use | Fields Used | Main Limitation |
| --- | --- | --- | --- |
| FAF5 state freight flows | OD intensity and regional imbalance | tons, ton-miles, origin state, destination state, mode | Annual aggregate, not tender-level |
| USDA AMS FVWTRK | Reefer rate and scarcity seed | spot truckload rates, destination cities, truck availability categories | Narrow equipment/commodity coverage |
| FMCSA HOS summary | Simplified feasibility clock | 11-hour drive, 14-hour duty, 10-hour reset | Simplified; omits split sleeper, recap, home-time |

## 6. Operational Feasibility Layer

Version 0.2 adds a first feasibility layer:

- **Individual trucks:** fleet state is a set of trucks, not only regional
  counts.
- **Pickup reach:** each load has a stochastic origin-market deadhead distance.
- **Appointment windows:** pickup and delivery earliest/latest times constrain
  feasibility.
- **HOS:** simplified property-carrier clocks use 11 driving hours, 14 duty
  hours, and 10-hour reset breaks.
- **Yard delays:** pickup and dropoff delays are sampled from a mixture with
  common short delays and occasional long delays.

This layer is intentionally simpler than a full dispatch simulator. It excludes
road closures, route-level traffic, split sleeper rules, driver home time, team
drivers, and maintenance.

The full benchmark keeps all feasibility features enabled. Ablation runs disable
one feature at a time only to measure sensitivity; they are not proposed as
alternative benchmark definitions.

## 7. Reference Policies

### Reject All

Reject every load. This is a lower-bound sanity check.

### Accept All Feasible

Accept every load that can be assigned at decision time. This isolates
operational feasibility from future-value reasoning.

### Myopic Margin

Accept when immediate margin is non-negative.

### Bid-Price Heuristic

Accept when immediate margin plus destination-origin future-value delta clears
zero.

### Linear Surrogate

Train a dependency-free ridge linear model on offline rollout incremental-value
labels.

### Selective Cascade

Use the surrogate for most loads and escalate to rollout near the decision
boundary or when truck supply is scarce.

### Finite Rollout Teacher

Evaluate accept and reject branches using common-random-number stochastic
future simulations and a bid-price base policy. The teacher is a stochastic
benchmark, not an oracle.

## 8. Metrics

Primary metrics:

- closed-loop profit,
- profit retention versus rollout teacher,
- mean and p95 decision latency,
- rollout-call share for cascades.

Feasibility metrics:

- infeasible accept attempts,
- pickup-window misses,
- delivery-window misses,
- no-truck outcomes,
- deadhead miles,
- HOS rest hours,
- yard-delay hours.

Statistical reporting:

- report seed count,
- report train/eval seed pairs,
- report mean, standard deviation, and 95% confidence intervals,
- include the full benchmark manifest.

## 9. Experimental Protocol

FreightBidBench v0.2 defines three scenarios:

**Table 2. Benchmark scenarios.**

| Scenario | Purpose |
| --- | --- |
| `mild` | Easy regime where myopic policies should be competitive. |
| `tight` | Moderate capacity scarcity where opportunity cost should matter. |
| `scarce` | High-demand, low-fleet regime where poor decisions compound. |

Presets:

**Table 3. Benchmark presets.**

| Preset | Use |
| --- | --- |
| `smoke` | Fast correctness check, not a reportable final result. |
| `standard` | Local development and preliminary benchmark result. |
| `paper` | Main result preset for the paper. |

Command:

```bash
python3 scripts/run_freightbidbench.py --preset standard --output-dir benchmark_runs/standard_v02
```

Outputs:

- `freightbidbench_policy_runs.csv`,
- `freightbidbench_static_label_fit.csv`,
- `freightbidbench_policy_summary.csv`,
- `freightbidbench_frontier_summary.csv`,
- `freightbidbench_manifest.json`,
- `freightbidbench_report.md`.

## 10. Results

The current v0.2 standard run used three train/eval seed pairs across the
`mild`, `tight`, and `scarce` scenarios. It used 600 rollout-label decisions per
train/eval stream and evaluated the full 72-hour online horizon. The run wrote
117 seed-level policy rows, 9 static-fit rows, 39 aggregate policy rows, and 21
cascade-frontier rows. Total runtime was 1,269.34 seconds.

### 10.1 Offline Label Fit

The simple linear surrogate is intentionally weak under the v0.2 feasibility
layer. Held-out accept/reject agreement was 58.8% in `mild`, 60.9% in `tight`,
and 68.3% in `scarce`. This is useful for the benchmark paper: the reference
surrogate is a baseline, not the contribution.

### 10.2 Policy Results

**Table 4. FreightBidBench v0.2 standard policy results.** Profit, latency, and
feasibility metrics are seed means over three train/eval seed pairs. Retention
is measured against the finite rollout teacher in the same scenario.

| Scenario | Policy | Mean Profit | Retention | Mean Latency ms | Infeasible | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `mild` | Reject all | $0 | 0.0% | 0.000 | 0.0 | 0 | 0 |
| `mild` | Accept all feasible | $1,082,891 | 101.7% | 0.040 | 0.0 | 2,053 | 783 |
| `mild` | Myopic | $1,082,891 | 101.7% | 0.000 | 323.7 | 2,053 | 783 |
| `mild` | Bid price | $1,083,424 | 101.8% | 0.001 | 312.0 | 2,050 | 782 |
| `mild` | Linear surrogate | $917,369 | 86.3% | 0.004 | 112.3 | 1,540 | 666 |
| `mild` | Cascade +/- $500 | $976,891 | 91.9% | 15.923 | 76.3 | 1,627 | 676 |
| `mild` | Rollout teacher | $1,064,003 | 100.0% | 45.574 | 0.0 | 1,840 | 676 |
| `tight` | Reject all | $0 | 0.0% | 0.000 | 0.0 | 0 | 0 |
| `tight` | Accept all feasible | $864,383 | 91.7% | 0.023 | 0.0 | 1,683 | 625 |
| `tight` | Myopic | $866,894 | 92.0% | 0.000 | 546.7 | 1,680 | 625 |
| `tight` | Bid price | $866,894 | 92.0% | 0.001 | 533.7 | 1,680 | 625 |
| `tight` | Linear surrogate | $739,135 | 78.5% | 0.004 | 87.3 | 1,217 | 539 |
| `tight` | Cascade +/- $500 | $812,794 | 86.3% | 11.069 | 34.3 | 1,363 | 538 |
| `tight` | Rollout teacher | $942,219 | 100.0% | 28.549 | 0.0 | 1,753 | 567 |
| `scarce` | Reject all | $0 | 0.0% | 0.000 | 0.0 | 0 | 0 |
| `scarce` | Accept all feasible | $714,150 | 94.3% | 0.016 | 0.0 | 1,373 | 512 |
| `scarce` | Myopic | $718,085 | 94.8% | 0.000 | 754.3 | 1,377 | 515 |
| `scarce` | Bid price | $718,085 | 94.8% | 0.001 | 740.0 | 1,377 | 515 |
| `scarce` | Linear surrogate | $487,441 | 64.4% | 0.004 | 40.3 | 813 | 373 |
| `scarce` | Cascade +/- $500 | $577,343 | 76.3% | 7.354 | 0.0 | 950 | 370 |
| `scarce` | Rollout teacher | $757,682 | 100.0% | 17.438 | 0.0 | 1,403 | 420 |

Two findings matter for the benchmark paper. First, feasibility metrics are not
secondary bookkeeping: myopic and bid-price policies create hundreds of
infeasible accept attempts in the v0.2 standard run. Second, rollout is much
slower under feasibility, with mean latency from 17.438 ms to 45.574 ms across
scenarios. This creates a clear latency-quality benchmark for future methods.

### 10.3 Cascade Frontier

The cascade frontier shows the tradeoff between rollout-call share and profit
retention. At the widest tested band, the cascade reached 97.1% retention in
`mild`, 91.8% in `tight`, and 90.5% in `scarce`. The result is not a final
method claim; it shows that the benchmark can expose meaningful frontier
differences across scenarios.

Generated figures:

**Figure 1. Profit retention by policy.**
`benchmark_runs/standard_v02/figures/profit_retention_by_policy.svg`

**Figure 2. Latency-profit frontier.**
`benchmark_runs/standard_v02/figures/latency_profit_frontier.svg`

**Figure 3. Rollout-call share versus profit retention.**
`benchmark_runs/standard_v02/figures/rollout_share_profit_frontier.svg`

**Figure 4. Infeasible accept attempts by policy.**
`benchmark_runs/standard_v02/figures/infeasible_accepts_by_policy.svg`

### 10.4 Operational Feasibility Ablation

We reran the standard preset with individual feasibility features disabled.
These are sensitivity tests, not recommended benchmark settings. Table 5 reports
the change in myopic profit relative to the full-feasibility benchmark.

**Table 5. Standard-preset feasibility ablation.** Full profit is the
full-feasibility myopic profit. Other columns report profit change after
disabling one or more feasibility features.

| Scenario | Full Profit | No Pickup Reach | No Windows | No HOS | No Yard Delays | Minimal Feasibility |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `mild` | $1.083M | +28.2% | +58.3% | +57.9% | +25.9% | +67.3% |
| `tight` | $0.867M | +35.1% | +124.3% | +115.5% | +32.5% | +144.9% |
| `scarce` | $0.718M | +30.9% | +194.0% | +154.5% | +27.9% | +218.6% |

The result is large: removing appointment windows raises myopic profit by
124.3% in `tight` and 194.0% in `scarce`; removing HOS raises myopic profit by
115.5% and 154.5% in the same scenarios. Thus, a benchmark that omits these
constraints can make simple fast policies look much stronger than they are
under operational feasibility.

Pickup reach and yard delays also matter, but primarily as cost and time
frictions. Removing them raises myopic profit by roughly 26-35% across the
three scenarios. The all-disabled `minimal_feasibility` variant is a much
easier problem: in `scarce`, myopic profit rises from $0.718M to $2.288M. This
supports the benchmark's central design choice: profit and latency should be
reported together with operational feasibility metrics.

## 11. Discussion

The central benchmark claim is that feasibility materially changes the
accept/reject problem. The ablation results strengthen this claim: appointment
windows and HOS constraints change the benchmark regime by more than the
current differences among several reference policies. A policy that looks
attractive under aggregate state-level availability can create pickup-window
misses, excess HOS rest, or yard-delay exposure once individual truck
feasibility is considered.

The latency result is also important: operational feasibility increases rollout
runtime. This makes FreightBidBench useful for studying selective evaluation,
surrogates, and other learning-augmented acceleration methods.

## 12. Limitations

FreightBidBench v0.2 is not a production dispatch simulator. It uses synthetic
loads, public calibration, simplified HOS clocks, state-level geography, and
reference Python latency. It does not model road closures, traffic, weather,
team drivers, split sleeper rules, maintenance, customer-specific facilities,
or private tender distributions.

These limitations should be stated as benchmark boundaries, not hidden.

## 13. Reproducibility

The benchmark release is designed around command-line reproduction rather than
manual notebook execution. From the `faster_planning/` directory, the v0.2
standard reference run is:

```bash
python3 scripts/run_freightbidbench.py --preset standard --output-dir benchmark_runs/standard_v02
```

Figures are generated from the resulting CSVs with:

```bash
python3 scripts/plot_freightbidbench.py --run-dir benchmark_runs/standard_v02
```

Every benchmark run writes a manifest containing:

- benchmark version,
- scenario-configuration version,
- policy-set version,
- command,
- Python version,
- source inputs,
- scenarios,
- seed pairs,
- default policies,
- cascade policy,
- evaluated policies,
- cascade bands,
- label limit,
- evaluation load limit,
- feasibility-layer version,
- output file paths,
- row counts.

Benchmark submissions should include the manifest and all summary CSVs.
The current reference manifest is
`benchmark_runs/standard_v02/freightbidbench_manifest.json`.

The standard feasibility ablation suite can be reproduced with:

```bash
python3 scripts/run_feasibility_ablation_suite.py --preset standard \
  --output-dir benchmark_runs/feasibility_ablations_standard
```

## 14. Conclusion

FreightBidBench provides a public, reproducible testbed for latency-aware
truckload bid acceptance. Its value is not that it solves the problem, but that
it gives researchers a shared environment where closed-loop profit, latency,
and operational feasibility can be compared under identical stochastic seeds.

## References

See `papers/references.bib`.
