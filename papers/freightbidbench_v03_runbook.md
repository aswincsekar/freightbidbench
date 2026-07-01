# FreightBidBench v0.3 Paper Runbook

## Artifact Layout

Use `benchmark_runs/paper_v03/` for assembled v0.3 paper tables. Do not write
v0.3 outputs into `benchmark_runs/paper_v02/`.

Recommended source artifacts:

- `benchmark_runs/v03_sweeps/methods_cascade_seed3_label200/` for the current
  methods frontier.
- `benchmark_runs/v03_sweeps/relaxed_bound_tight_full_rollout/` and
  `benchmark_runs/v03_sweeps/relaxed_bound_scarce_full_rollout/` for relaxed
  full-horizon ceilings.
- `benchmark_runs/hindsight_bound_smoke/` for the exact small-prefix diagnostic.

## Assemble Current Tables

```bash
make paper-v03-tables
```

This writes:

- `benchmark_runs/paper_v03/v03_methods_table.csv`
- `benchmark_runs/paper_v03/v03_relaxed_bound_table.csv`
- `benchmark_runs/paper_v03/v03_exact_hindsight_table.csv`
- `benchmark_runs/paper_v03/v03_paper_tables.md`

## Final Paper Run Sequence

1. Run the methods frontier with the frozen v0.3 config:

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

2. Run relaxed bounds for tight and scarce with rollout comparison:

```bash
python3 scripts/run_relaxed_hindsight_bound.py \
  --config configs/freightbidbench_v03_scenarios.json \
  --scenario tight \
  --policies accept_all_feasible,bid_price,rollout_teacher \
  --output-dir benchmark_runs/v03_sweeps/relaxed_bound_tight_full_rollout

python3 scripts/run_relaxed_hindsight_bound.py \
  --config configs/freightbidbench_v03_scenarios.json \
  --scenario scarce \
  --policies accept_all_feasible,bid_price,rollout_teacher \
  --output-dir benchmark_runs/v03_sweeps/relaxed_bound_scarce_full_rollout
```

3. Run exact DP on small prefixes. Increase `--max-loads` only if the state
   count stays tractable.

```bash
make hindsight-smoke
```

4. Assemble the table drafts:

```bash
make paper-v03-tables
```

## Interpretation Notes

Report exact hindsight and relaxed bounds separately. Exact DP is trustworthy
but small; relaxed full-horizon bounds are intentionally loose. The cascade
frontier should be reported per scenario because the best band differs between
`tight` and `scarce`.
