# Gap-Kernel Search (Theorem B(ii))

Instances searched: 3000 (seed 2). Certified positive duality gaps found: 2 (0.07%).

Certificate: LP value of the chain-packing relaxation (exact
Fraction simplex) equals min_lambda L(lambda) by Dantzig-Wolfe;
V* by exact joint enumeration. gap = LP - V* in exact rationals.

## Kernel (trial 1634): V* = 34, LP = 36 (= 36.000), gap = 2 (5.9% of V*)
```
trucks (id, market, avail, budget):
  T0: M2 avail=0 budget=2
  T1: M3 avail=1 budget=1
  T2: M1 avail=1 budget=2
loads (id, t, origin->dest, tt, reward):
  L0: t=0 M3->M1 tt=1 r=7
  L1: t=1 M1->M0 tt=2 r=10
  L2: t=1 M2->M1 tt=1 r=6
  L3: t=2 M0->M1 tt=1 r=14
  L4: t=3 M1->M2 tt=1 r=6
  L5: t=4 M3->M1 tt=2 r=9
  L6: t=5 M2->M0 tt=2 r=13
```

## Kernel (trial 502): V* = 43, LP = 44 (= 44.000), gap = 1 (2.3% of V*)
```
trucks (id, market, avail, budget):
  T0: M2 avail=0 budget=2
  T1: M1 avail=0 budget=2
  T2: M0 avail=0 budget=2
loads (id, t, origin->dest, tt, reward):
  L0: t=0 M1->M0 tt=2 r=8
  L1: t=1 M0->M2 tt=2 r=14
  L2: t=1 M2->M0 tt=2 r=10
  L3: t=2 M1->M0 tt=1 r=9
  L4: t=2 M0->M1 tt=1 r=11
  L5: t=4 M1->M0 tt=1 r=12
  L6: t=5 M1->M0 tt=1 r=8
```

