# FreightBidBench v0.3 Terminal Fleet-Value Sweep

## Purpose

Phase A2 makes end-of-horizon fleet position part of realized reward. The
terminal value is computed from the existing state-value signal, which is based
on FAF outbound intensity and `data/processed/faf_state_imbalance_2024.csv`,
then multiplied by `terminal_value_weight`.

The calibration gate is that `accept_all_feasible` should retain no more than
95% of rollout profit on `tight` and `scarce`, because greedy feasible
acceptance should pay for weak final positioning.

## Sweep Commands

One-seed full-horizon sweep:

```bash
python3 scripts/run_terminal_value_sweep.py \
  --preset standard \
  --scenarios tight,scarce \
  --weights 0,0.1,0.25,0.5,1.0 \
  --seed-count 1 \
  --label-limit 20 \
  --cascade-bands 0 \
  --output-dir benchmark_runs/v03_sweeps/terminal_value_fullseed1
```

Three-seed check at the selected value:

```bash
python3 scripts/run_terminal_value_sweep.py \
  --preset standard \
  --scenarios tight,scarce \
  --weights 0.25 \
  --seed-count 3 \
  --label-limit 20 \
  --cascade-bands 0 \
  --output-dir benchmark_runs/v03_sweeps/terminal_value_fullseed3
```

## Result

The one-seed sweep showed that `0.1` had only a small effect, while `0.25`
created a materially larger gap in `tight` without making `reject_all`
competitive. Larger weights widened terminal-value influence but began to make
the terminal term more prominent than needed for A2.

The three-seed check at `0.25` produced:

| Scenario | Accept All Feasible | Rollout Teacher | Retention | Terminal Value: Accept All | Terminal Value: Rollout | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `tight` | $894,944 | $998,035 | 89.7% | $30,561 | $32,581 | yes |
| `scarce` | $741,078 | $789,637 | 93.9% | $26,928 | $29,583 | yes |

## Decision

Freeze `terminal_value_weight` at `0.25` in
`configs/freightbidbench_v03_scenarios.json` and bump the scenario contract to
`scenario-v0.3.1`. This clears the A2 gate while keeping the terminal value as
a secondary reward component rather than the main source of profit.
