# GitHub Release Notes

## Suggested Repository Description

Feasibility-calibrated benchmark for real-time truckload bid acceptance.

## Suggested Topics

- freight
- truckload
- logistics
- stochastic-optimization
- operations-research
- benchmark
- approximate-dynamic-programming

## Initial Release Checklist

1. Create an empty public GitHub repository, or make the existing repository
   public.
2. Add the remote:

   ```bash
   git remote add origin git@github.com:aswincsekar/freightbidbench.git
   ```

3. Push the current branch:

   ```bash
   git push -u origin main
   ```

4. Confirm the GitHub Actions CI run passes.
5. Create the first tag:

   ```bash
   git tag -a v0.2.1 -m "FreightBidBench v0.2.1"
   git push origin v0.2.1
   ```

6. Create the GitHub release from `v0.2.1` and attach or point readers to the
   tracked `benchmark_runs/paper_v02` reference outputs.
7. If Zenodo is enabled for the repository, confirm that it minted a DOI for
   the `v0.2.1` release and add the DOI to the README and paper draft.

## Data Note

The repository tracks processed calibration tables and generated benchmark
artifacts. Raw public downloads are excluded by `.gitignore`; see
`data/raw/README.md`. Code and documentation are Apache-2.0; generated
benchmark artifacts are CC BY 4.0.
