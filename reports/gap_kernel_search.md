# Gap-Kernel Search (Theorem B(ii))

Instances searched: 3000 (seed 1). Certified positive duality gaps found: 1 (0.03%).

Certificate: LP value of the chain-packing relaxation (exact
Fraction simplex) equals min_lambda L(lambda) by Dantzig-Wolfe;
V* by exact joint enumeration. gap = LP - V* in exact rationals.

## Kernel (trial 2880): V* = 41, LP = 89/2 (= 44.500), gap = 7/2 (8.5% of V*)
```
trucks (id, market, avail, budget):
  T0: M1 avail=1 budget=2
  T1: M2 avail=0 budget=2
  T2: M0 avail=1 budget=2
loads (id, t, origin->dest, tt, reward):
  L0: t=0 M1->M2 tt=1 r=6
  L1: t=1 M0->M1 tt=2 r=13
  L2: t=1 M2->M0 tt=2 r=6
  L3: t=4 M0->M2 tt=1 r=14
  L4: t=4 M1->M0 tt=1 r=7
  L5: t=5 M2->M1 tt=1 r=14
```
Fractional certificate (truck, chain loads, value, weight):
```
  T0 {L4} val=7 x=1/2
  T1 {L2,L3} val=20 x=1/2
  T1 {L5} val=14 x=1/2
  T2 {L3,L5} val=28 x=1/2
  T2 {L1,L4} val=20 x=1/2
```


## Dual certificate (added 2026-07-28)

Exact LP dual pinning LP = 89/2 (so the gap is exactly 7/2):

```
load duals   λ = (0, 0, 0, 21/2, 7, 9/2)   for L0..L5
truck duals  μ = (0, 19/2, 13)             for T0..T2
dual value   Σλ + Σμ = 22 + 45/2 = 89/2
```

Dual feasibility μ_k + Σ_{t∈S} λ_t ≥ val(S) holds for each of the
eight feasible chains, with equality on the five packed chains.
Verified in exact rationals (see `k1 duals` extraction against
`scripts/find_gap_kernel.py` chain enumeration; zero violations).
