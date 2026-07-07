# GitHub Release Notes

## Suggested Repository Description

Public-calibrated benchmark for real-time truckload bid acceptance, with
operational feasibility, hindsight ceilings, and a latency-aware policy cascade.

## Suggested Topics

- freight
- truckload
- logistics
- stochastic-optimization
- operations-research
- benchmark
- approximate-dynamic-programming

## Release Checklist (current: v0.3.0)

1. (One-time; skip if the repository is already public) Create an empty public
   GitHub repository, or make the existing repository public.
2. Add the remote (one-time):

   ```bash
   git remote add origin git@github.com:aswincsekar/freightbidbench.git
   ```

3. Push the current branch:

   ```bash
   git push -u origin main
   ```

4. Confirm the GitHub Actions CI run passes.
5. Tag the release:

   ```bash
   git tag -a v0.3.0 -m "FreightBidBench v0.3.0"
   git push origin v0.3.0
   ```

6. Create the GitHub release from `v0.3.0` and point readers to the tracked
   `benchmark_runs/paper_v03` assembled tables and the
   `benchmark_runs/v03_sweeps/methods_cascade_seed10_label200`
   reference manifest. (The prior `v0.2.1` release remains for historical
   comparison.)
7. If Zenodo is enabled for the repository, confirm that it minted a DOI for
   the `v0.3.0` release and add the DOI to the README, `CITATION.cff`, and the
   paper's Data Availability Statement.

## Data Note

The repository tracks processed calibration tables and generated benchmark
artifacts. Raw public downloads are excluded by `.gitignore`; see
`data/raw/README.md`. Code and documentation are Apache-2.0; generated
benchmark artifacts are CC BY 4.0.
