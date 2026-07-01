# FreightBidBench v0.3 Service-Failure Penalty Sweep

## Purpose

Phase A1 makes failed accept attempts economically real. The calibration gate is
that `myopic_margin` and `bid_price` should fall strictly below
`accept_all_feasible` on `tight` and `scarce`, because feasibility-blind
policies should pay for unserviceable tenders.

## Sweep Commands

Short 250-load prefix:

```bash
python3 scripts/run_service_failure_penalty_sweep.py \
  --preset smoke \
  --scenarios tight,scarce \
  --penalties 0,10,25,50 \
  --seed-count 1 \
  --label-limit 20 \
  --eval-load-limit 250 \
  --output-dir benchmark_runs/v03_sweeps/service_failure_penalty_eval250
```

Full-horizon three-seed check at the selected value:

```bash
python3 scripts/run_service_failure_penalty_sweep.py \
  --preset standard \
  --scenarios tight,scarce \
  --penalties 10 \
  --seed-count 3 \
  --label-limit 20 \
  --cascade-bands 0 \
  --output-dir benchmark_runs/v03_sweeps/service_failure_penalty_fullseed3
```

The low label limit keeps calibration runtime bounded. The A1 ordering depends
on realized failed accepts, not surrogate label quality.

## Result

The 250-load sweep showed that `$0` preserves the v0.2 tie, while the smallest
tested nonzero value, `$10`, flips the ordering in both `tight` and `scarce`.
The larger `$25` and `$50` values only widen the same effect.

The full-horizon three-seed check at `$10` produced:

| Scenario | Accept All Feasible | Myopic | Bid Price | Myopic Gap | Bid-Price Gap | Ordering Met |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `tight` | $864,383 | $861,274 | $861,391 | -$3,109 | -$2,992 | yes |
| `scarce` | $714,150 | $710,405 | $710,495 | -$3,744 | -$3,654 | yes |

The corresponding mean service-failure penalty costs were `$5,620` for myopic
and `$5,503` for bid price in `tight`, and `$7,680` for myopic and `$7,590` for
bid price in `scarce`.

## Decision

Freeze `service_failure_penalty_dollars` at `$10` in
`configs/freightbidbench_v03_scenarios.json` for A1. This is the smallest
tested value that satisfies the ordering gate on the full-horizon three-seed
check. The final v0.3 standard or paper run should use the normal label limit,
but this value is sufficient to proceed to A2 terminal fleet value.
