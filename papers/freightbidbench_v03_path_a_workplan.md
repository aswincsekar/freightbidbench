# FreightBidBench v0.3 — Path A Workplan: Ship-Sooner Submission (CompOR / TR-E)

Date: 2026-06-30. Status: planning. Supersedes the methodology-track
ambitions of `freightbidbench_v03_path_b_workplan.md` for this submission.

## 1. Objective

Bring the existing v0.3 draft
(`papers/freightbidbench_v03_benchmark_paper.md`) to submission quality
for **Computers & Operations Research** (primary) or **Transportation
Research Part E** (secondary). Target: a submission that clears desk
review and reaches referees, expecting one minor/major revision cycle.
Estimated acceptance at these venues after this plan: ~75–90%.

The headline story is unchanged and already written: a **latency-aware
surrogate→rollout cascade** ("the super-fast load planner") that recovers
≥98% of rollout profit at a fraction of rollout latency, on a
public-calibrated, dependency-free, closed-loop truckload bid-acceptance
benchmark with explicit operational feasibility and three economic layers,
anchored by exact + relaxed + Lagrangian hindsight ceilings.

## 2. Scope decisions

### In scope (load-bearing for CompOR/TR-E credibility)

- **Rigor cleanup** of the draft (notation, trivial propositions, weak
  citations, undefined terms). Path B §8 checklist.
- **Scarce Lagrangian bound** to remove the asymmetric "—" in Table 4
  (Theorem 1 currently only demonstrated on `tight`).
- **Statistical backing** for headline retention claims: modest seed bump
  (3 → ~10) plus paired-bootstrap CI95 and sign-test p-values. Removes the
  draft's own "preliminary … larger run in preparation" caveat.
- **Scoped calibration evidence** converting "public-calibrated" from
  assertion to a short shown section using FAF/USDA data already in the
  repo (load-mix and lane-mileage vs. FAF; price vs. USDA AMS ranges).
- **Modest literature tightening**: drop weak cascade citations, add the
  anytime-algorithm lineage, ~30–35 refs total (not 50–60).
- **LaTeX build parity + final table assembly** for a submittable PDF.

### Cut for this venue (deferred; was Path B / TransSci-only)

- **Theorem 2 (cascade regret bound)** and oracle-band validation. The
  cascade stays descriptive with the existing limit characterization
  (Prop 3). This is the single biggest scope cut that makes "ship sooner"
  real.
- **30-seed program.** ~10 seeds with CIs is defensible here.
- **Full ATRI/FMCSA operational-calibration appendix.** Replaced by the
  scoped FAF/USDA calibration above.
- **Literature expansion to 50–60 refs.**

These are not abandoned — they remain the upgrade path to Transportation
Science if a referee pushes for more, or for a follow-on paper.

## 3. Critical path (dependency-aware)

Two long-pole **compute jobs** gate the final tables; everything else is
writing that runs in parallel while they execute.

```
Day 0   ── Launch BOTH background runs ──────────────────────────┐
            A. scarce Lagrangian bound  (longest pole, multi-hour)│
            B. methods rerun seed≈10 + CIs (multi-hour)           │
                                                                  │
Days 0–N (in parallel with runs) ── pure writing, no compute dep ─┤
            C. rigor cleanup pass (§8 checklist)                  │
            D. scoped calibration section (FAF/USDA, repo data)   │
            E. literature tightening                              │
                                                                  │
After A,B land ───────────────────────────────────────────────────┘
            F. reassemble all tables (make paper-v03-tables + new)
            G. fold scarce-Lagrangian + CIs into draft, retune claims
            H. LaTeX parity, build PDF, internal read-through
            I. submission checklist + cover letter
```

Sequencing rule: **kick off A and B first** (they dominate wall-clock),
then do C/D/E while they run, then F→I once results land.

## 4. Workstreams

### A. Scarce Lagrangian bound  (compute, longest pole)

The `tight` bound exists (`benchmark_runs/lagrangian_bound_full_v6_warm`,
$1,885,043, 20.7% tighter than LP, validity PASS). The `scarce` row of
Table 4 is "—". Run the same two-stage cold+warm subgradient schedule on
`scarce` (fleet/loads larger than tight → expect ≥ tight's ~3.4h wall).

```bash
python3 scripts/run_lagrangian_bound.py \
  --config configs/freightbidbench_v03_scenarios.json \
  --scenario scarce \
  --lp-bound-reference 2675525 \
  --rollout-reference <scarce rollout profit at the eval seed> \
  --output-dir benchmark_runs/lagrangian_bound_scarce_full
# then warm-start a second stage via --initial-duals-csv / --iter-offset
```

Exit criterion: a valid bound (≥ rollout) for `scarce`, ideally also
tighter than its LP bound. **Fallback if it doesn't tighten or doesn't
finish in budget:** report `tight` as the demonstrated Theorem-1 result
and state the `scarce` bound honestly as LP-only — still publishable,
just less symmetric. Decide at the run's first convergence check.

### B. Methods rerun with confidence intervals  (compute)

Current headline table is 3-seed point estimates (`methods_cascade_
seed3_label200`). Bump seeds and attach paired-bootstrap CI95 +
sign-tests via the existing `analyze_policy_deltas.py` machinery
(`make deltas`).

```bash
python3 scripts/run_freightbidbench.py \
  --config configs/freightbidbench_v03_scenarios.json \
  --preset standard --scenarios tight,scarce \
  --seed-count 10 --label-limit 200 \
  --cascade-bands 0,250,500,700,900 \
  --output-dir benchmark_runs/v03_sweeps/methods_cascade_seed10_label200
```

Reinstate `mild` as a numeric negative control (cheap, referee-expected).
Exit criterion: every headline retention number carries mean, CI95, n,
and a sign-test p-value; the draft's "preliminary" caveat is deleted.
Tune `--seed-count` down if wall-clock is prohibitive — even 6–8 with CIs
beats 3 without.

### C. Rigor cleanup pass  (writing, no compute dep)

Work the Path B §8 checklist that applies regardless of venue:
- Resolve the ω collision (terminal weight vs. random scenario → use ξ
  for the scenario) and the ℓ overload (load tuple vs. truck location).
- Demote Prop 1 to a remark or sharpen it (it is currently near-trivial).
- Define V(·) explicitly (one equation from FAF outbound intensity +
  imbalance table).
- Specify the feasibility tie-break rule (§3.2) and surrogate training
  protocol (ridge λ, standardization, train/eval split — §6.1).
- Fix Prop 3(a) proof (rollout-rejects-on-empty, not "vanishing
  probability under mixing") and weaken the continuity assumption to
  account for discrete-feature atoms.
- Add a notation table.

Exit criterion: an internal proof/notation read-through with no undefined
symbols and no trivially-true "propositions" dressed as results.

### D. Scoped calibration section  (writing + light analysis)

Convert "public-calibrated" from assertion to evidence using data already
in the repo (`data/processed/v1_usda_faf_mapped_lanes.csv`,
`faf_state_imbalance_2024.csv`; pipeline in `inspect_public_sources.py`):
- Origin-state market shares vs. FAF outbound flow shares.
- Lane-mileage distribution vs. FAF tonnage-weighted mileage.
- Linehaul price distribution vs. USDA AMS truck-rate ranges.

Keep it to one section/short appendix with 2–3 figures or tables. Defer
ATRI/FMCSA operational calibration to a stated limitation/future-work
line. Exit criterion: a reader can see the calibration is real, not
claimed.

### E. Literature tightening  (writing)

Drop the weak cascade citations (Derrow-Pinion ETA, Alonso-Mora
ride-pooling) and add the anytime-algorithm / deliberation-control
lineage (Boddy & Dean 1989, Zilberstein 1996, Horvitz, Russell & Wefald)
plus Viola & Jones for the cascade framing. Target ~30–35 refs. Verify
every citation resolves in `papers/references.bib`.

### F–I. Assembly and submission

- F: regenerate tables (`make paper-v03-tables`) and add the scarce
  Lagrangian + CI columns.
- G: fold new numbers into the .md draft; retune abstract/§8 claims to
  CI-anchored language ("99.9% (CI95 …)").
- H: bring `papers/freightbidbench_v03_benchmark_paper.tex` to parity with
  the .md and build via `make paper-pdf` (needs pdflatex/bibtex).
- I: venue submission checklist + cover letter; confirm code/artifact
  release link and manifest reproducibility statement.

## 5. Decision points

- **D1 (scarce Lagrangian first convergence check):** if not tightening
  vs LP within the run budget, fall back to tight-only Theorem 1 framing
  (Workstream A fallback) rather than burning days on solver tuning.
- **D2 (after seed bump):** if the qualitative ordering or the ≥98%
  cascade retention does NOT survive more seeds, report the honest
  numbers and adjust the abstract — do not overclaim. The cascade story
  survives even at modestly lower retention as long as it dominates the
  standalone surrogate and the best simple baseline.

## 6. Effort estimate

- Compute (A, B): launch day 0, land within 1–2 days of wall-clock
  (mostly unattended, background).
- Writing (C, D, E): ~1–1.5 weeks of focused work, overlapping the runs.
- Assembly (F–I): ~2–4 days once runs land.
- **Calendar total: ~2–3 weeks to a submittable manuscript**, vs. ~5
  months for the full Path B / TransSci program.
```

## 7. What we are explicitly NOT blocking on

The benchmark artifact (v0.2.1) is already released and immutable under
`benchmark_runs/paper_v02/`. Nothing in this plan touches that reference
run. The v0.3 contract is frozen at `scenario-v0.3.2` /
`policy-set-v0.3.0`; this plan adds evidence and rigor, it does not change
the public contract, so no version bump is required unless a sweep reveals
a needed recalibration (treat as a D2-class decision if it arises).
