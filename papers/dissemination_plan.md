# FreightBidBench v0.3 — Dissemination Plan

Decision (2026-07): keep **one OR-journal paper** (Computers & Operations
Research, primary), maximize reach via **preprints**, and add **OR
conference talks** (non-archival, no exclusivity conflict). NeurIPS
Datasets & Benchmarks was considered and deferred (would require splitting
the paper).

Exclusivity rule: journals = one at a time; preprints = post all; OR
conference *talks* = non-archival, fine alongside the journal. Do NOT also
submit to Transportation Research Record (that's an archival journal).

---

## Track 1 — Preprints (post all, in parallel)

### 1a. arXiv — in progress
Primary `cs.LG`, cross-list `math.OC`, `cs.AI`. Bundle:
`dist/freightbidbench_v03_arxiv_source.tar.gz`. Blocked only on the cs.LG
endorsement (code sent to endorser).

### 1b. Optimization Online — no endorsement needed
Submit at optimization-online.org (create account → Submit).
- **Title:** Latency-Aware Bid Acceptance under Operational Feasibility: A
  Public Benchmark with Hindsight Ceilings
- **Area (pick from their live list):** Applications — OR and Management
  Sciences (Transportation); secondary: Stochastic Programming /
  Approximate Dynamic Programming.
- **Abstract:** use the journal abstract.
- **Keywords:** online truckload bid acceptance; closed-loop stochastic
  optimization; approximate dynamic programming; information-relaxation
  bounds; latency-aware policy cascade; public benchmark.
- **File:** the built PDF.

### 1c. SSRN — reaches transport/logistics + business audience
Submit at ssrn.com (Author portal → Submit a paper). Route to the
**Transportation Research Network** / **Operations Research eJournal**.
- Title, abstract, keywords: as above.
- Optional JEL codes: `C61` (optimization techniques), `R41`
  (transportation: demand, supply, congestion), `L91` (transportation).
- Disclosure: SSRN shows affiliation — Bubba AI (consistent with the
  competing-interest statement).

---

## Track 2 — Journal (anchor)

**Computers & Operations Research** via Editorial Manager (see
`submission_checklist.md`). One at a time; fallbacks in order: IJOC,
TR-E / EURO J. Transportation & Logistics, EJOR, NRL.

---

## Track 3 — OR conference talks (non-archival; present + journal both fine)

### 3a. TRB Annual Meeting (freight/logistics audience) — DEADLINE ~AUG 1, 2026
Confirmed: **TRB 2027 Annual Meeting**, Jan 10–14, 2027, Washington DC.
Paper submission site **open July 1 – August 1, 2026** (site:
trb.secure-platform.com/a/page/TRBPaperReview). Decisions in October;
accepted final papers due Nov 20.
- ⚠️ TRB wants a **full paper** (not just an abstract), in the **TRB
  template**, ~7,500-word equivalent (each table/figure ≈ 250 words), with
  a TRB-format title page. Our CompOR PDF must be **reformatted** to hit
  this — the main effort for this deadline.
- Election: choose **"presentation only"** (do NOT elect Transportation
  Research Record publication — TRR is archival and would conflict with the
  CompOR submission). Presentation-only + the online compendium is normally
  fine alongside an Elsevier journal, but confirm on the CompOR guide.
- Committee fit: freight transportation / logistics / freight systems.

### 3b. INFORMS Annual Meeting (TSL society)
Abstract submission usually opens winter–spring for the fall meeting.
Verify the current cycle's deadline. Submit a talk abstract to the
**Transportation Science & Logistics (TSL)** cluster. Non-archival.

**Short talk abstract (~60 words, INFORMS program format):**
> We introduce FreightBidBench, a public-calibrated, dependency-free
> benchmark for real-time truckload bid acceptance under closed-loop fleet
> state, hours-of-service, appointment windows, and yard delays. We provide
> exact and Lagrangian-per-truck hindsight ceilings and a latency-aware
> surrogate-to-rollout cascade that recovers ~98% of rollout profit at
> roughly half the latency. All results reproduce from the Python standard
> library.

**Longer talk abstract (~140 words, TRB / extended format):**
> Online truckload bid acceptance requires accept/reject decisions in
> seconds under closed-loop fleet state, hours-of-service limits,
> appointment windows, and stochastic yard delays. Public, reproducible
> benchmarks for this problem are scarce. We present FreightBidBench, a
> public-calibrated, dependency-free, closed-loop benchmark built from
> Freight Analysis Framework and USDA truck-rate data, in which operational
> feasibility and economics (service-failure penalty, terminal fleet value,
> price-premium windows) are explicit and versioned. We anchor policy
> evaluation with two hindsight ceilings — an exact small-prefix dynamic
> program and a Lagrangian-per-truck information-relaxation bound 20–39%
> tighter than an LP relaxation — and introduce a latency-aware
> surrogate-to-rollout cascade that recovers ~98% of rollout profit at
> roughly half the decision latency, statistically indistinguishable from
> the rollout teacher on the tight scenario. Everything reproduces from the
> Python standard library.

---

## Suggested sequence

1. Now: post Optimization Online + SSRN (PDF is ready; no endorsement gate).
2. Now: check the TRB deadline (~Aug 1) — if open, submit the talk
   (presentation-only) this cycle.
3. When arXiv endorsement clears: post the arXiv preprint.
4. Submit CompOR via Editorial Manager.
5. Submit INFORMS TSL talk when that cycle opens.
