# FreightBidBench v0.3 Surrogate Feature Track

## Purpose

Phase C starts with the dependency-free `surrogate_linear` baseline before
adding optional stronger learners. The goal is to make the stdlib surrogate see
the economics introduced in Phase A: service-failure penalties, terminal fleet
value, and daily price-premium timing.

## Change

The linear surrogate now receives additional features:

- feasibility probe features: `feasible_accept`, `service_failure_risk`,
  `service_failure_penalty`, and `realized_profit_if_feasible`;
- temporal price features: `price_wave_multiplier` and
  `price_window_premium`;
- terminal-value features: `terminal_origin_value`,
  `terminal_destination_value`, and `terminal_delta`.

Surrogate-only decisions also include a feasibility guard: if the linear model
predicts accept but the copied-fleet feasibility probe fails, the policy
rejects instead of paying a service-failure penalty. Rollout escalations are
unchanged.

## Commands

One-seed checks with larger rollout-label sets:

```bash
python3 scripts/run_freightbidbench.py \
  --config configs/freightbidbench_v03_scenarios.json \
  --preset standard \
  --scenarios tight \
  --seed-count 1 \
  --label-limit 200 \
  --cascade-bands 0,500 \
  --output-dir benchmark_runs/v03_sweeps/surrogate_features_guard_tight_label200

python3 scripts/run_freightbidbench.py \
  --config configs/freightbidbench_v03_scenarios.json \
  --preset standard \
  --scenarios scarce \
  --seed-count 1 \
  --label-limit 200 \
  --cascade-bands 0,500 \
  --output-dir benchmark_runs/v03_sweeps/surrogate_features_guard_scarce_label200
```

Three-seed cascade frontier check:

```bash
python3 scripts/run_freightbidbench.py \
  --config configs/freightbidbench_v03_scenarios.json \
  --preset standard \
  --scenarios tight,scarce \
  --seed-count 3 \
  --label-limit 200 \
  --cascade-bands 0,250,500,700,900 \
  --output-dir benchmark_runs/v03_sweeps/methods_cascade_seed3_label200
```

## One-Seed Result

| Scenario | Best Simple Retention | Surrogate Retention | Cascade 500 Retention | Cascade 500 Latency | Rollout Latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | 87.5% | 91.1% | 100.5% | 21.27 ms | 31.27 ms |
| `scarce` | 75.8% | 72.1% | 96.2% | 16.72 ms | 20.14 ms |

Static rollout-label agreement was `81.0%` on `tight` and `70.5%` on
`scarce` with 200 train labels. The standalone linear surrogate is still weak
on scarce, but the cascade result is promising because the surrogate filters
easy decisions while escalating enough cases to recover most rollout value.

## Three-Seed Frontier

| Scenario | Best Simple Retention | Surrogate Retention | Best Low-Latency Cascade | Retention | Latency | Rollout Latency |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| `tight` | 88.9% | 94.3% | band `0` | 99.9% | 7.88 ms | 31.67 ms |
| `scarce` | 85.6% | 84.1% | band `700` | 98.0% | 16.58 ms | 23.27 ms |

The balanced scarce point is band `500`, which reaches `98.3%` of rollout at
`16.68 ms`; the high-retention scarce point is band `900`, which reaches
`99.6%` of rollout at `18.00 ms`. On tight, band `0` is already the best
frontier point: it retains `99.9%` of rollout while using rollout on `34.8%`
of decisions.

The three-seed run confirms that the cascade story is real enough for v0.3:
simple policies sit around `85-89%`, standalone surrogate is cheap but uneven,
and cascade policies recover most rollout value at lower average latency.

## Decision

Keep the enhanced stdlib surrogate as the v0.3 dependency-free methods anchor.
Do not claim the standalone surrogate solves scarce; report it as a baseline.
Use per-scenario cascade bands in the paper instead of a single global band:
band `0` is the tight frontier point, while scarce needs band `700` for the
lowest-latency point above `98%` or band `900` for the highest-retention point.
The next methods step is an optional
stronger learner behind a separate script or flag, with CI and smoke targets
remaining stdlib-only.
