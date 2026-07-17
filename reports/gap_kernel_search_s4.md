# Gap-Kernel Search (Theorem B(ii))

Instances searched: 3000 (seed 4). Certified positive duality gaps found: 1 (0.03%).

Certificate: LP value of the chain-packing relaxation (exact
Fraction simplex) equals min_lambda L(lambda) by Dantzig-Wolfe;
V* by exact joint enumeration. gap = LP - V* in exact rationals.

## Kernel (trial 2962): V* = 43, LP = 87/2 (= 43.500), gap = 1/2 (1.2% of V*)
```
trucks (id, market, avail, budget):
  T0: M1 avail=0 budget=2
  T1: M0 avail=1 budget=2
  T2: M2 avail=0 budget=2
  T3: M0 avail=0 budget=2
loads (id, t, origin->dest, tt, reward):
  L0: t=1 M1->M3 tt=1 r=10
  L1: t=1 M0->M3 tt=2 r=9
  L2: t=1 M0->M1 tt=2 r=9
  L3: t=2 M0->M3 tt=2 r=13
  L4: t=3 M1->M0 tt=1 r=7
  L5: t=4 M0->M2 tt=1 r=14
```

