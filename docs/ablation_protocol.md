# FreightBidBench Feasibility Ablations

FreightBidBench can disable individual operational-feasibility features so
the paper can report how much each layer changes the benchmark.

## CLI Flags

The public runner supports:

| Flag | Effect |
| --- | --- |
| `--disable-pickup-reach` | Removes origin-market pickup deadhead time and cost. |
| `--disable-time-windows` | Stops enforcing pickup and delivery appointment windows. |
| `--disable-hos` | Stops enforcing simplified 11/14/10 HOS clocks. |
| `--disable-yard-delays` | Removes stochastic pickup/dropoff yard delays and delay cost. |

Each run records the active and disabled features in
`freightbidbench_manifest.json`.

## Local Smoke Ablation

Use this before changing benchmark logic:

```bash
python3 scripts/run_feasibility_ablation_suite.py \
  --preset smoke \
  --label-limit 20 \
  --eval-load-limit 50 \
  --cascade-bands 0,500 \
  --output-dir benchmark_runs/feasibility_ablations_smoke
```

The wrapper writes:

- one normal FreightBidBench output directory per ablation variant,
- `feasibility_ablation_index.csv`,
- `feasibility_ablation_policy_summary.csv`.

## Paper Ablation

For a paper table, use at least the `standard` preset:

```bash
python3 scripts/run_feasibility_ablation_suite.py \
  --preset standard \
  --output-dir benchmark_runs/feasibility_ablations_standard
```

The `paper` preset is stronger but expensive because it multiplies the full
benchmark by six feasibility variants.

## Reporting Rule

Report ablations as benchmark sensitivity, not as production validation. The
correct claim is that these feasibility features change the synthetic
closed-loop benchmark behavior under controlled seeds.
