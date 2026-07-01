# FreightBidBench v0.3 Demand-Wave Sweep

## Purpose

Phase A3 tests whether temporal demand structure creates a clearer timing
problem for future-aware policies. The implementation supports piecewise
hour-of-day load-count waves, optional origin and destination lane-weight
multipliers, and optional price-premium windows.

The calibration gate is that the best simple policy should retain no more than
90% of rollout profit on both `tight` and `scarce`.

## Sweep Commands

One-seed global count-wave sweep:

```bash
python3 scripts/run_demand_wave_sweep.py \
  --mode global \
  --preset standard \
  --scenarios tight,scarce \
  --amplitudes 0,0.25,0.5,0.75 \
  --seed-count 1 \
  --label-limit 20 \
  --cascade-bands 0 \
  --output-dir benchmark_runs/v03_sweeps/demand_waves_fullseed1
```

One-seed market, combined, and price-premium sweeps:

```bash
python3 scripts/run_demand_wave_sweep.py --mode market ...
python3 scripts/run_demand_wave_sweep.py --mode combined ...
python3 scripts/run_demand_wave_sweep.py --mode price ...
```

Three-seed validation for the selected price-premium candidates:

```bash
python3 scripts/run_demand_wave_sweep.py \
  --mode price \
  --preset standard \
  --scenarios tight,scarce \
  --amplitudes 0.25,0.5 \
  --seed-count 3 \
  --label-limit 20 \
  --cascade-bands 0 \
  --output-dir benchmark_runs/v03_sweeps/demand_waves_price_selected_seed3
```

## Result

The no-wave control already clears the simple-policy gate on the one-seed
standard check:

| Scenario | Best Simple | Retention | Gap |
| --- | --- | ---: | ---: |
| `tight` | `accept_all_feasible` | 89.8% | 10.19 pp |
| `scarce` | `accept_all_feasible` | 85.3% | 14.68 pp |

Nonzero global, Texas-market, and combined count/market waves did not clear the
gate on both scenarios. Price-premium waves were more effective because they
make preserving capacity for a predictable future window economically valuable.

The smallest tested price premium, amplitude `0.25`, missed on `tight` in the
three-seed validation:

| Scenario | Best Simple | Retention | Gap | Gate |
| --- | --- | ---: | ---: | --- |
| `tight` | `accept_all_feasible` | 90.8% | 9.18 pp | no |
| `scarce` | `accept_all_feasible` | 88.7% | 11.27 pp | yes |

Amplitude `0.5` cleared the gate on the same three-seed validation:

| Scenario | Best Simple | Retention | Gap | Gate |
| --- | --- | ---: | ---: | --- |
| `tight` | `accept_all_feasible` | 88.9% | 11.07 pp | yes |
| `scarce` | `accept_all_feasible` | 85.5% | 14.47 pp | yes |

## Decision

Freeze the price-premium schedule at amplitude `0.5` in
`configs/freightbidbench_v03_scenarios.json` and bump the scenario contract to
`scenario-v0.3.2`. The frozen schedule keeps demand counts flat, leaves
off-peak prices unchanged, and applies a daily `1.5x` price multiplier during
hours `[8, 16)`.
