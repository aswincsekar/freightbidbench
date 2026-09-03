# v0.4 analysis (regenerated from raw CSVs)

## Table 1 inputs: methods comparison

### mild (n = 30 pairs)
- bid_price: retention 99.1%, latency 1.308 us/decision
- dual_price: retention 99.1%, latency 37.477 us/decision
- dual_price_vf: retention 101.8%, latency 38.245 us/decision
- rollout_teacher: retention 100.0%, latency 111.66 ms
- surrogate_linear: retention 98.3%, latency 105.845 us/decision
- paired vf-surrogate: +3.5 pp [CI95 +2.4, +4.5]; $+47,873 [CI95 +33,262, +61,750]
- Wilcoxon p = 0.000; sign test 26/30 wins, p = 0.000

### scarce (n = 30 pairs)
- bid_price: retention 85.9%, latency 1.211 us/decision
- dual_price: retention 86.6%, latency 16.664 us/decision
- dual_price_vf: retention 90.2%, latency 17.814 us/decision
- rollout_teacher: retention 100.0%, latency 48.03 ms
- surrogate_linear: retention 91.1%, latency 74.760 us/decision
- paired vf-surrogate: -0.9 pp [CI95 -3.1, +1.4]; $-9,625 [CI95 -31,736, +13,376]
- Wilcoxon p = 0.329; sign test 12/30 wins, p = 0.362

### tight (n = 30 pairs)
- bid_price: retention 91.1%, latency 1.256 us/decision
- dual_price: retention 91.2%, latency 24.725 us/decision
- dual_price_vf: retention 95.4%, latency 25.444 us/decision
- rollout_teacher: retention 100.0%, latency 74.45 ms
- surrogate_linear: retention 93.4%, latency 80.704 us/decision
- paired vf-surrogate: +2.1 pp [CI95 +0.5, +3.7]; $+25,095 [CI95 +6,072, +43,794]
- Wilcoxon p = 0.019; sign test 19/30 wins, p = 0.200

## Table 2 inputs: certificates

### tight (10 instances)
- dual_price_vf: certified >= 60.1% of hindsight optimum (57.0--63.2)
- rollout_teacher: certified >= 62.8% of hindsight optimum (60.3--66.9)
- mean bound-solve time: 1019 minutes

### scarce (10 instances)
- dual_price_vf: certified >= 57.6% of hindsight optimum (53.3--61.3)
- rollout_teacher: certified >= 63.6% of hindsight optimum (61.1--65.2)
- mean bound-solve time: 1177 minutes

## Table 3 inputs: see scripts/aggregate_scaling_crossfit.py (cross-fitted, sound-certified scaling cells)
