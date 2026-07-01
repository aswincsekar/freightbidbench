# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

FreightBidBench v0.2.1: a public-calibrated synthetic benchmark for real-time truckload bid acceptance under closed-loop fleet state, appointment windows, simplified HOS clocks, and stochastic yard delays. Released as a standalone artifact ahead of the method paper.

The benchmark is intentionally **dependency-free at runtime** — Python 3.10+ standard library only. Do not add third-party dependencies (numpy, pandas, scikit-learn, etc.) without strong justification; the dependency-free reference implementation is a feature, not a limitation.

## Common commands

All commands run from the repo root. The `Makefile` is the default interface.

| Command | Purpose |
| --- | --- |
| `make test` | `py_compile` all scripts/tests, then run the `unittest` suite. |
| `make smoke` | Tiny benchmark contract (1 seed, 5 labels, 10 eval loads) into `benchmark_runs/ci_smoke`. Use after touching benchmark contracts or manifest schema. |
| `make quickstart` | Smoke preset + figures into `benchmark_runs/quickstart`. |
| `make standard` | Standard preset (3 seeds, all scenarios) into `benchmark_runs/standard_v02`. |
| `make deltas` | Paired-seed bootstrap policy deltas vs rollout teacher for `benchmark_runs/paper_v02`. |
| `make hindsight-smoke` | v0.3 exact hindsight-bound prototype. |
| `make paper-pdf` | Build the LaTeX paper in `papers/build/` (requires `pdflatex`/`bibtex`). |

Run a single test:

```bash
python3 -m unittest tests.test_feasibility.FeasibilityTests.test_hos_reset_inserted
```

Direct runner invocation (the CLI exposes ablations, scenario overrides, cascade-band overrides, etc.):

```bash
python3 scripts/run_freightbidbench.py --preset smoke --output-dir benchmark_runs/my_run
```

Ablation suite wrapper (runs each `--disable-*` flag and aggregates):

```bash
python3 scripts/run_feasibility_ablation_suite.py --preset smoke --output-dir benchmark_runs/ablations_smoke
```

## Architecture

### Script layering

`scripts/` contains all runtime logic. The scripts form a layered import graph — the top-level CLI is thin and most logic lives in the deeper modules:

- `run_freightbidbench.py` — public benchmark CLI. Reads the versioned config, dispatches presets/scenarios, writes the six-file output contract.
- `run_surrogate_cascade.py` — the **policy decision layer**. `choose_action()` is the dispatch site for every named policy (`myopic_margin`, `bid_price`, `surrogate_linear`, `cascade_surrogate_rollout`, etc.). Adding a policy means adding a branch here that returns `(wants_accept, score, stage_name)`.
- `run_rollout_teacher.py` — finite-lookahead Monte Carlo rollout with common-random-number accept/reject branches. The "teacher" labels used to train the surrogate and as the retention denominator.
- `run_closed_loop_baselines.py` — defines `Scenario`, simple baseline policies, and the closed-loop simulator core. Imported by everything above.
- `run_experimental_package.py` — packaging/feature extraction layer used by the benchmark runner.
- `freight_feasibility.py` — the v0.2 feasibility layer: per-truck records, pickup reach, appointment windows, simplified 11/14/10 HOS, stochastic yard delays. Disabling any feature is a CLI flag, not a code change.
- `run_hindsight_bound.py` — v0.3 exact-DP hindsight ceiling for truncated load streams.
- `analyze_policy_deltas.py` / `plot_freightbidbench.py` — post-run analysis and figure generation (consume the CSV outputs only).
- `inspect_public_sources.py` — pipeline that produces `data/processed/v1_usda_faf_mapped_lanes.csv` and `data/processed/faf_state_imbalance_2024.csv` from public FAF/USDA inputs.

### Versioned contract

`configs/freightbidbench_v02_scenarios.json` is the single source of truth for scenario parameters, presets, the default public policy set, the cascade policy, cascade bands, and the default first seed. The runner copies these values into every manifest.

Three version strings live in that file: `benchmark_version`, `scenario_config_version`, `policy_set_version`. **Bump the relevant version whenever you change the public contract** (scenario numerics, default policies, cascade bands, preset seed counts). Manifests and the paper reference these versions for reproducibility.

### Policy contract

A policy is a branch in `choose_action()` (`scripts/run_surrogate_cascade.py`) that returns:

```python
return wants_accept, score, stage_name
```

It may read load fields, fleet state, lane table, scenario config, state future-value features, and an optional trained surrogate. It **must not mutate `load` or `fleet`** — fleet mutation happens only after the benchmark applies the decision and the feasibility layer succeeds. Policies that escalate to rollout must report the `rollout` stage so cascade frontier metrics stay comparable.

### Output contract

Every benchmark run writes six files to its output directory:

- `freightbidbench_policy_runs.csv` — per-cell rows (scenario × seed pair × policy × cascade band).
- `freightbidbench_static_label_fit.csv` — held-out surrogate fit.
- `freightbidbench_policy_summary.csv` — aggregate means / std / 95% CI.
- `freightbidbench_frontier_summary.csv` — latency-profit frontier per cascade band.
- `freightbidbench_manifest.json` — **the reproducibility anchor**. Records command, all three version strings, seed pairs, source input paths, feasibility config, scenarios, output paths, row counts.
- `freightbidbench_report.md` — human-readable summary.

Column definitions are pinned in `docs/csv_column_dictionary.md`. The golden smoke contract (`make smoke` with `--cascade-bands 0`) must produce exactly **1 static-fit row, 7 policy-run rows, 7 policy-summary rows, 1 cascade-frontier row** — this is asserted by `tests/test_cli_smoke.py` against `tests/golden/tiny_smoke_expected.json`.

### Data flow

Public inputs sit in `data/raw/`; processed seed tables in `data/processed/`. The runner consumes the processed CSVs directly. Re-running `inspect_public_sources.py` only matters when the upstream FAF/USDA sources change.

## Reference artifacts — treat as immutable

`benchmark_runs/paper_v02/` is the **v0.2.1 paper reference run**. Do not silently overwrite it. If a change affects the published manifest, summary CSVs, or figures, update the paper draft (`papers/freightbidbench_v02_benchmark_paper.tex`), `FREIGHTBIDBENCH.md`, and the relevant docs in the same PR. The release SHA and arXiv bundle (`freightbidbench_arxiv_check/`, `dist/`) are pinned to this run.

`benchmark_runs/standard/` is the older v0.1 run (no HOS/window feasibility). Kept for historical comparison.

## Testing conventions

- `unittest` only — no pytest. Tests live in `tests/test_*.py`.
- `tests/test_cli_smoke.py` invokes the benchmark CLI as a **subprocess** and asserts manifest shape against `tests/golden/tiny_smoke_expected.json`. If you change manifest fields or smoke row counts, regenerate the golden fixture in the same commit.
- Tests must be deterministic — pass explicit seeds and small limits to keep CI under the smoke budget.
- Run `make smoke` (not just `make test`) whenever you change benchmark contracts, presets, or manifest schema.

## Style

- Python 3.10+, 4-space indent, snake_case functions/variables, PascalCase classes.
- One-purpose scripts with explicit `argparse` CLI flags. Match the existing `scripts/` naming pattern (lowercase + underscores).
- Commit subjects are short and imperative ("Add arXiv source bundle", "Tighten FreightBidBench manifest contract"). One logical change per commit.
