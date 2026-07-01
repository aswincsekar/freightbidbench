# FreightBidBench v0.3 Paper Workplan

## Paper Objective

FreightBidBench v0.3 should move from a feasibility-calibration paper to a
stronger benchmark-and-methods paper. The v0.2 result showed that operational
feasibility is first-order, but it also exposed that simple policies sit too
close to the finite rollout teacher for the cascade thesis to be convincing.
The v0.3 paper should make the decision problem sharper before making stronger
claims about acceleration.

## Core v0.3 Claims To Earn

- The benchmark has a diagnostic ceiling above rollout, not only retention
  against a finite stochastic teacher.
- Service failures are economically meaningful, not only counted as feasibility
  events.
- End-of-horizon fleet position has value, so terminal repositioning matters.
- Temporal demand waves create cases where future-aware decisions separate
  from immediate-margin heuristics.
- A stronger surrogate or cascade can be evaluated against rollout, hindsight,
  and the best simple baseline.

## Initial Milestones

1. Add a realized-seed hindsight diagnostic for small streams.
   Status: started in `scripts/run_hindsight_bound.py`.

2. Add explicit service-failure penalties.
   A policy that accepts an unserviceable tender should pay a configurable
   penalty or cancellation cost. This will make infeasible accepts part of
   reward, not only diagnostics. Calibration sweeps are run with
   `scripts/run_service_failure_penalty_sweep.py` and summarized under
   `benchmark_runs/v03_sweeps/service_failure_penalty/`. A1 is currently
   frozen at `$10` based on `reports/service_failure_penalty_sweep_report.md`.

3. Add terminal fleet value.
   End-of-horizon trucks should receive a destination value based on downstream
   demand, scarcity, or public-calibrated imbalance. This should reduce
   artificial end-horizon myopia. A2 is currently frozen at weight `0.25`
   based on `reports/terminal_value_sweep_report.md`.

4. Add temporal demand structure.
   Introduce scenario-level demand waves by market, hour, or day segment so
   repositioning and timing can be tested under controlled seeds. A3 is frozen
   as a daily price-premium window at amplitude `0.5` in
   `scenario-v0.3.2`; see `reports/demand_wave_sweep_report.md`.

5. Replace the linear surrogate baseline.
   Keep the dependency-free baseline, but add a stronger method track that can
   be optional for the paper experiments. The stdlib surrogate has been updated
   with v0.3 economic features and a feasibility guard. A three-seed cascade
   frontier now recovers at least `98%` of rollout on tight/scarce at lower
   average latency; see
   `reports/surrogate_feature_track_report.md`.

## Hindsight-Bound Prototype

The first v0.3 diagnostic is a limited exact accept/reject optimizer:

```bash
make hindsight-smoke
```

It solves a truncated realized stream under the current v0.2 deterministic
assignment rule and writes:

- `benchmark_runs/hindsight_bound_smoke/hindsight_bound_summary.csv`
- `benchmark_runs/hindsight_bound_smoke/hindsight_bound_decisions.csv`
- `benchmark_runs/hindsight_bound_smoke/hindsight_policy_comparison.csv`
- `benchmark_runs/hindsight_bound_smoke/hindsight_bound_report.md`

This is intentionally a small-instance diagnostic. It should be used to verify
that rollout and simple policies sit below a realized-seed ceiling before we
scale to stronger formulations.

The full-horizon diagnostic is a separate relaxed ceiling:

```bash
make relaxed-bound-smoke
```

It writes:

- `benchmark_runs/relaxed_bound_smoke/relaxed_bound_summary.csv`
- `benchmark_runs/relaxed_bound_smoke/relaxed_bound_load_terms.csv`
- `benchmark_runs/relaxed_bound_smoke/relaxed_bound_policy_comparison.csv`
- `benchmark_runs/relaxed_bound_smoke/relaxed_bound_report.md`

This bound is intentionally loose and should be reported as a relaxation, not
as an achievable plan. Phase B status and one-seed full-horizon checks are
summarized in `reports/relaxed_bound_report.md`.

## Experiment Design For The Paper

The v0.3 paper should report three anchors for each scenario:

- best simple baseline, such as `accept_all_feasible`, `myopic_margin`, or
  `bid_price`;
- rollout teacher;
- realized-seed hindsight diagnostic on a tractable subset or relaxed bound.

Tables should include profit, service-failure cost, infeasible attempts,
terminal fleet value, latency, and confidence intervals. Figures should show
latency-profit tradeoffs only after the scenario changes create a real gap
between simple policies and future-aware policies.

## Claim Discipline

Do not claim production validation, regulatory-complete HOS, private tender
fit, or rollout optimality. The v0.3 claim should be narrower: under a
public-calibrated, versioned benchmark with explicit feasibility costs and a
hindsight diagnostic, future-aware bid policies can be compared reproducibly
against simple baselines and latency-aware approximations.
