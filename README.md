# FreightBidBench

FreightBidBench is a public-calibrated synthetic benchmark for real-time
truckload bid acceptance under closed-loop fleet state, appointment-window,
hours-of-service, and yard-delay feasibility.

## Install

FreightBidBench uses only the Python standard library at runtime.

```bash
git clone https://github.com/aswincsekar/freightbidbench.git && cd freightbidbench && make test
```

## Reproduce v0.3

The v0.3 paper artifacts are assembled under `benchmark_runs/paper_v03/` from
the ten-seed methods reference run in
`benchmark_runs/v03_sweeps/methods_cascade_seed10_label200/`, whose
`freightbidbench_manifest.json` is the canonical reproducibility anchor.

Run the ten-seed methods frontier:

```bash
python3 scripts/run_freightbidbench.py \
  --config configs/freightbidbench_v03_scenarios.json \
  --preset standard --scenarios mild,tight,scarce \
  --seed-count 10 --label-limit 200 --cascade-bands 0,250,500,700,900 \
  --output-dir benchmark_runs/v03_sweeps/methods_cascade_seed10_label200
```

Compute paired policy deltas and the public-data calibration report:

```bash
python3 scripts/analyze_policy_deltas.py \
  --run-dir benchmark_runs/v03_sweeps/methods_cascade_seed10_label200 --cascade-band 500
make calibration-report
```

Assemble paper tables and build the paper:

```bash
make paper-v03-tables
make paper-v03-pdf
```

The v0.2.1 release remains available for historical comparison under
`benchmark_runs/paper_v02/` (git tag `v0.2.1`).

## Reproduce v0.4 (certified dual-price methods)

The v0.4 methods paper (arXiv:2607.16891) adds the `dual_price` and
`dual_price_vf` policies, the Lagrangian dual-price fitting pipeline,
and exact-certificate kernel search. Headline commands:

```bash
scripts/run_30seed_program.sh
```

```bash
python3 scripts/run_lagrangian_bound.py --workers 4
```

Price/value tables come from `scripts/fit_dual_prices.py` and
`scripts/fit_value_togo.py`; scaling cells from
`configs/freightbidbench_v04_dev_scaling.json`; kernel search from
`scripts/find_gap_kernel.py`. The public v0.4 contract is
`configs/freightbidbench_v04_scenarios.json` (`policy-set-v0.4.0`);
artifacts live under `benchmark_runs/v04_dev/`.

## Main Artifacts

| Path | Purpose |
| --- | --- |
| `scripts/run_freightbidbench.py` | Benchmark runner with smoke, standard, and paper presets. |
| `scripts/freight_feasibility.py` | Feasibility layer: truck state, pickup reach, appointment windows, HOS clocks, yard delays. |
| `scripts/run_lagrangian_bound.py` | Lagrangian-per-truck information-relaxation hindsight bound. |
| `scripts/analyze_policy_deltas.py` | Paired-seed bootstrap policy-difference analysis. |
| `scripts/analyze_calibration.py` | Public FAF/USDA calibration cross-checks. |
| `configs/freightbidbench_v03_scenarios.json` | v0.3 scenario, preset, policy-set, seed, and cascade-band contract. |
| `benchmark_runs/v03_sweeps/methods_cascade_seed10_label200/` | Ten-seed methods reference run and manifest. |
| `benchmark_runs/paper_v03/` | Assembled v0.3 paper tables. |
| `papers/freightbidbench_v03_benchmark_paper.tex` | v0.3 LaTeX paper. |
| `papers/references.bib` | BibTeX references. |
| `benchmark_runs/paper_v02/` | v0.2.1 historical reference run. |

## License

Code and documentation are licensed under Apache-2.0; see `LICENSE`.
Generated benchmark artifacts, manifests, CSV outputs, reports, and figures are
licensed under CC BY 4.0; see `LICENSE-DATA`.

## Citation

Check out the release tag matching the paper you are reproducing:

- Benchmark (v0.3): arXiv:2607.07343,
  <https://arxiv.org/abs/2607.07343> — tag `v0.3.0`
- Certified dual-price methods (v0.4): arXiv:2607.16891,
  <https://arxiv.org/abs/2607.16891> — tag `v0.4.2`

```bash
git checkout v0.4.2
```

Repository citation metadata is in `CITATION.cff`.
