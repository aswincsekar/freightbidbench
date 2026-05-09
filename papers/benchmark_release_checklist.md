# FreightBidBench v0.2.1 Release Checklist

## Required For First Benchmark Paper

- [x] Public benchmark runner: `scripts/run_freightbidbench.py`
- [x] Feasibility layer: `scripts/freight_feasibility.py`
- [x] Paper benchmark run: `benchmark_runs/paper_v02`
- [x] Reproducibility manifest: `benchmark_runs/paper_v02/freightbidbench_manifest.json`
- [x] Aggregate policy summary CSV
- [x] Aggregate frontier summary CSV
- [x] Dependency-free plotting script
- [x] Standard-run SVG figures
- [x] Benchmark protocol doc: `FREIGHTBIDBENCH.md`
- [x] First manuscript draft: `papers/freightbidbench_v02_benchmark_paper.md`
- [x] LaTeX manuscript draft: `papers/freightbidbench_v02_benchmark_paper.tex`
- [x] BibTeX references: `papers/references.bib`

## Before External Release

- [x] Decide repository layout for public release.
- [x] Add Apache-2.0 code/documentation license.
- [x] Add CC BY 4.0 generated-artifact license note.
- [x] Add a citation file, e.g. `CITATION.cff`.
- [x] Add a minimal CI smoke command:
  `python3 scripts/run_freightbidbench.py --preset smoke --output-dir benchmark_runs/smoke_ci`
- [x] Add a clean-data note explaining which raw files can be redistributed.
- [x] Confirm generated paper-run CSVs contain synthetic benchmark outputs only.
- [x] Add figure captions to the final manuscript format.
- [ ] Tighten related work with final venue citation style.
- [x] Run the heavier `paper` preset.
- [x] Add appendix with manifest schema and CSV column dictionary.
- [x] Install local LaTeX toolchain and compile the draft once.
- [x] Add local feasibility ablation flags and smoke wrapper.
- [x] Run standard feasibility ablation suite locally.
- [x] Fold standard feasibility ablation results into the manuscript drafts.
- [x] Add policy-extension documentation.
- [x] Resolve current LaTeX citation and layout warnings.
- [x] Push to GitHub.
- [x] Create `v0.2.1` tag on GitHub.
- [x] Confirm remote CI passes.

## Claims To Keep

- FreightBidBench is a reproducible benchmark for latency-aware truckload bid acceptance.
- Public calibration gives transparent freight-flow and refrigerated-rate structure.
- Operational feasibility materially changes the benchmark.
- Finite rollout is a stochastic benchmark, not an oracle.
- Reference policies are baselines, not state-of-the-art claims.

## Claims To Avoid

- Do not claim real carrier profit validation.
- Do not claim generated tenders reproduce a private load board.
- Do not claim the simplified HOS layer is regulatory-complete.
- Do not claim rollout is optimal.
- Do not claim the linear surrogate is competitive with modern ML methods.
