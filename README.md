# FreightBidBench

FreightBidBench is a public-calibrated synthetic benchmark for real-time
truckload bid acceptance under closed-loop fleet state, appointment-window,
hours-of-service, and yard-delay feasibility.

## Install

FreightBidBench uses only the Python standard library at runtime.

```bash
git clone https://github.com/aswincsekar/freightbidbench.git && cd freightbidbench && make test
```

## Reproduce v0.2.1

The v0.2.1 paper run and generated artifacts are under
`benchmark_runs/paper_v02/`. The reference manifest is:

```text
benchmark_runs/paper_v02/freightbidbench_manifest.json
```

Run the paper preset:

```bash
python3 scripts/run_freightbidbench.py --preset paper --output-dir benchmark_runs/paper_v02
```

Generate figures:

```bash
python3 scripts/plot_freightbidbench.py --run-dir benchmark_runs/paper_v02
```

Compute paired policy deltas:

```bash
python3 scripts/analyze_policy_deltas.py --run-dir benchmark_runs/paper_v02
```

Build the paper draft:

```bash
make paper-pdf
```

## Main Artifacts

| Path | Purpose |
| --- | --- |
| `scripts/run_freightbidbench.py` | Benchmark runner with smoke, standard, and paper presets. |
| `scripts/freight_feasibility.py` | v0.2 feasibility layer for truck state, pickup reach, appointment windows, HOS clocks, and yard delays. |
| `scripts/analyze_policy_deltas.py` | Paired-seed bootstrap policy-difference analysis. |
| `configs/freightbidbench_v02_scenarios.json` | Scenario, preset, policy-set, seed, and cascade-band contract. |
| `benchmark_runs/paper_v02/freightbidbench_manifest.json` | v0.2.1 reference manifest. |
| `benchmark_runs/paper_v02/freightbidbench_policy_summary.csv` | Aggregate policy results. |
| `benchmark_runs/paper_v02/freightbidbench_policy_delta_summary.csv` | Paired deltas versus rollout teacher. |
| `benchmark_runs/paper_v02/figures/` | Generated SVG benchmark figures. |
| `papers/freightbidbench_v02_benchmark_paper.tex` | LaTeX paper draft. |
| `papers/references.bib` | BibTeX references. |

## License

Code and documentation are licensed under Apache-2.0; see `LICENSE`.
Generated benchmark artifacts, manifests, CSV outputs, reports, and figures are
licensed under CC BY 4.0; see `LICENSE-DATA`.

## Citation

Use the GitHub release tag `v0.2.1` for exact reproduction:

```bash
git checkout v0.2.1
```

After the arXiv version is live, cite the arXiv identifier and this release tag
together. Repository citation metadata is in `CITATION.cff`.
