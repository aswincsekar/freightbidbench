# Cover Letter — v0.4 methods paper (Transportation Science)

Draft (2026-07-28). Finalize after the adversarial pass and arXiv v2;
build to PDF the same way as `build/cover_letter_compor.tex`.

**To:** The Editor-in-Chief, *Transportation Science*
**Re:** Submission of an original research article

Dear Editor,

I would like to submit my manuscript "Certified-Gap Dual-Price Policies
for Real-Time Truckload Bid Acceptance with Relocating,
Clock-Constrained Resources" for consideration in *Transportation
Science*.

The problem: a truckload carrier receives a load tender and has seconds
to answer. The best operational methods (Monte Carlo rollout) are
accurate but cost tens to hundreds of milliseconds per decision, and
they say nothing about how far from optimal they are. This paper asks
the harder question: how close to optimal can a real-time policy be,
and can that closeness be certified per instance?

The paper uses one Lagrangian relaxation twice — as an upper bound and
as a source of dual prices for a microsecond acceptance policy — so
every run ships with a certified optimality gap. Three results make
this rigorous. First, the certificate is valid for any duals, any
discretization, and any surrogate quality. Second, in the subcritical
fluid regime the policy's same-time spatial-gradient rule is exactly
fluid complementary slackness and the policy is asymptotically optimal;
the proof needs no mean-field machinery because dual-price policies are
state-blind, and the same linear-programming basis stability explains
why fitted prices are portable across sample paths. Third, certificates
have limits: a three-truck kernel with an exact rational certificate
and a replication lemma shows per-resource duality slack can stay
bounded away from zero at every fleet size. On a public benchmark's
pre-registered confirmation set of thirty fresh paired seeds — code
and analysis frozen and pushed before any confirmatory result — the
policy, which needs no rollout labels, beats a rollout-trained
surrogate on one scenario and is statistically indistinguishable
from it on the other two, deciding roughly a thousand times faster.
A development-set effect that did not survive confirmation is
reported as such in the paper.

The model sits outside the reusable-resource and weakly-coupled lines
this journal knows well: the resources relocate and carry
hours-of-service clocks, so service capability is a controlled state
variable. I believe the combination — model, policy-with-certificate,
two-sided theory, and a public reproducible evaluation — is a fit for
*Transportation Science*.

This manuscript is original and is not under review elsewhere. It is
posted as a preprint (arXiv:2607.16891). It is distinct from a
companion benchmark paper (arXiv:2607.07343, under review at a
computational OR journal): the companion contributes the evaluation
artifact and reports no methods theorems; the present paper contributes
the policy, the certificates, and all three theorems, and uses the
benchmark only as its test bed. There is no overlap in claimed
contributions.

One disclosure up front: I am Cofounder and CTO of Bubba AI, which
builds AI-based load-planning products in this domain. The study uses
only public data and open-source code, and Bubba AI had no role in the
study design, analysis, or the decision to publish; the full statement
is in the manuscript's declarations.

All code, manifests, and every table regenerate from documented
commands at github.com/aswincsekar/freightbidbench.

Thank you for considering it.

Sincerely,

Aswin Chandrasekaran
Cofounder and CTO, Bubba AI
Pune, India
aswin@bubba.ai
