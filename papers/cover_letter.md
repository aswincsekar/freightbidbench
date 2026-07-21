# Cover Letter — FreightBidBench v0.3 (Computers & Operations Research)

Submitted PDF built at `papers/build/cover_letter_compor.pdf` (source:
`papers/build/cover_letter_compor.tex`).

**To:** The Editors, *Computers & Operations Research*
**Re:** Submission of an original research article

Dear Editors,

I would like to submit my manuscript "Latency-Aware Bid Acceptance under
Operational Feasibility: A Public Benchmark with Hindsight Ceilings" for
consideration in *Computers & Operations Research*.

The problem is simple to state: a truckload carrier or broker receives a
load tender and has seconds to accept or reject it. The right answer
depends on where the fleet is, how much drive time each driver has left,
and whether the appointment windows can actually be met. There has been
no public, reproducible benchmark for this closed-loop problem — routing
benchmarks are static, and dynamic-fleet studies run on private operator
data.

The paper contributes three things. First, FreightBidBench: a closed-loop
benchmark calibrated entirely from public FAF and USDA data, with
operational feasibility and economics inside the reward, and
dependency-free — every result reproduces from the Python standard
library. Second, hindsight ceilings: a Lagrangian-per-truck
information-relaxation bound that is 20.7–39.3% tighter than an LP
relaxation, so policies are measured against a meaningful ceiling rather
than only against a heuristic teacher. Third, a latency-aware
surrogate-to-rollout cascade that recovers about 98% of rollout profit at
40–56% of its decision latency, evaluated across paired seeds with
bootstrap confidence intervals.

I believe this fits the journal well: an OR decision problem paired with
a computational artifact, where the code, manifests, and every table in
the paper regenerate from documented commands at
github.com/aswincsekar/freightbidbench.

The manuscript is original and is not under review anywhere else. It is
posted as a preprint (arXiv:2607.07343). One disclosure I want to make up
front: I am Cofounder and CTO of Bubba AI, which builds AI-based
load-planning products in this domain. The study uses only public data
and open-source code, and Bubba AI had no role in the study design,
analysis, or the decision to publish; the full statement is in the
manuscript's Declaration of Competing Interest.

Thank you for considering it.

Sincerely,

Aswin Chandrasekaran
Cofounder and CTO, Bubba AI
Pune, India
aswin@bubba.ai
