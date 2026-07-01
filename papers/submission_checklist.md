# FreightBidBench v0.3 — Submission Checklist

Primary venue: **Computers & Operations Research** (Elsevier).
Fallback: **Transportation Research Part E** (Elsevier).

## Manuscript content

- [x] Abstract states benchmark + two hindsight ceilings + cascade, with
      CI-anchored headline numbers.
- [x] Problem formulation (MDP: state, action, feasibility, reward,
      objective) with a notation table.
- [x] `V(·)` terminal signal defined by equation; feasibility tie-break
      rule stated; surrogate training protocol specified.
- [x] Prop 1 (L1 regret), Prop 2 (relaxed-bound validity), Prop 3 (cascade
      limit, corrected `κ=−1` statement + no-atom assumption), Theorem
      (Lagrangian-per-truck bound).
- [x] Experiments: 10-seed methods table + frontier, paired-bootstrap CIs,
      `mild` negative control, layer ablation (3-seed, labeled), hindsight
      diagnostics, sensitivity.
- [x] Appendix A reproducibility (commands, versions, manifest schema).
- [x] Appendix B calibration validation (FAF/USDA cross-checks).
- [x] Limitations: synthetic data, simplified HOS, loose relaxed bound,
      lane-coverage concentration, dependency-free scope.

## Build & artifacts

- [x] PDF builds clean via `make paper-v03-pdf` (20 pp, no undefined
      refs/citations).
- [x] `references.bib` — all cites resolve; unused entries pruned.
- [x] Assembled tables regenerate via `make paper-v03-tables` (10-seed).
- [x] Calibration report regenerates via `make calibration-report`.
- [x] `make test` green; `make smoke` contract intact.

## Before upload (author actions)

- [ ] De-anonymize / anonymize per venue policy; fill author block and
      affiliations (currently "The Author(s)").
- [ ] Confirm the public code/artifact URL is live and matches the release
      SHA cited in the paper.
- [ ] Convert `cover_letter.md` to the portal's required format.
- [ ] Elsevier declarations: author contributions, competing interests,
      data availability statement, funding.
- [ ] Suggest 3–4 reviewers (dynamic fleet management / stochastic routing).
- [ ] Optional pre-submission polish: reword the two remaining sub-inch
      overfull prose lines in §6; re-run the 3-seed layer ablation at 10
      seeds if a referee asks for seed-count consistency.

## Known open items (non-blocking, honest to leave)

- Layer-ablation table (Table 1) is 3-seed while the methods table is
  10-seed. Labeled as such; acceptable for this venue.
- ATRI/FMCSA operational-metric calibration deferred (stated in Appendix B).
- Theorem 2 (cascade regret bound) intentionally out of scope for this
  venue; it is the upgrade path to Transportation Science.
