# Repository Guidelines

## Project Structure & Module Organization
Core logic lives in `scripts/`. The main entry point is `scripts/run_freightbidbench.py`, with supporting analysis and plotting scripts alongside it. Scenario and preset definitions live in `configs/`. Tests are in `tests/`, with golden fixtures under `tests/golden/`. Generated benchmark outputs belong in `benchmark_runs/`; treat these as artifacts, not hand-edited source. Paper sources and release assets live in `papers/`, `dist/`, and `reports/`. Public input and processed reference data are under `data/raw/` and `data/processed/`.

## Build, Test, and Development Commands
Use the `Makefile` targets as the default interface:

- `make test` compiles Python files and runs the `unittest` suite.
- `make smoke` runs the tiny CI benchmark contract into `benchmark_runs/ci_smoke`.
- `make quickstart` generates a local smoke run plus figures in `benchmark_runs/quickstart`.
- `make standard` runs the standard preset and writes outputs to `benchmark_runs/standard_v02`.
- `make deltas` computes paired policy deltas for `benchmark_runs/paper_v02`.
- `make paper-pdf` builds the LaTeX draft in `papers/build/`.

For a direct run, use `python3 scripts/run_freightbidbench.py --preset smoke --output-dir benchmark_runs/my_run`.

## Coding Style & Naming Conventions
Target Python 3.10+ and keep dependencies to the standard library unless there is a strong reason otherwise. Follow existing style: 4-space indentation, descriptive snake_case for functions and variables, PascalCase for classes, and one-purpose scripts with explicit CLI flags. Keep file names lowercase with underscores, matching the current `scripts/` and `tests/` patterns.

## Testing Guidelines
Tests use `unittest`. Add new coverage in `tests/test_*.py`, and keep fixtures or expected outputs in `tests/golden/` when exact manifests or CSV-derived summaries matter. Prefer deterministic tests with explicit seeds and small limits so they stay CI-friendly. Run `make test` before opening a PR; run `make smoke` when changing benchmark contracts, manifests, or preset behavior.

## Commit & Pull Request Guidelines
Recent commits use short, imperative subjects such as `Add arXiv source bundle` and `Tighten FreightBidBench manifest contract`. Follow that pattern and keep each commit scoped to one logical change. PRs should state what changed, why it changed, and which commands you ran to verify it. Include artifact paths or screenshots only when outputs or figures changed.

## Data & Artifact Handling
Do not silently overwrite reference outputs in `benchmark_runs/paper_v02` or `dist/` without noting the reproduction impact. If a change affects published artifacts, update the relevant docs, manifests, and paper references in the same PR.
