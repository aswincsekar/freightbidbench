# v0.4 analysis (regenerated from raw CSVs)

## Table 1 inputs: methods comparison

### mild (n = 30 pairs)
- bid_price: retention 99.1%, latency 1.308 us/decision
- dual_price: retention 99.1%, latency 36.913 us/decision
- dual_price_vf: retention 101.8%, latency 37.607 us/decision
- rollout_teacher: retention 100.0%, latency 111.66 ms
- surrogate_linear: retention 98.3%, latency 105.845 us/decision
- paired vf-surrogate: +3.5 pp [CI95 +2.4, +4.5]; $+48,004 [CI95 +33,428, +61,820]
- Wilcoxon p = 0.000; sign test 26/30 wins, p = 0.000

### scarce (n = 30 pairs)
- bid_price: retention 85.9%, latency 1.211 us/decision
- dual_price: retention 86.6%, latency 16.687 us/decision
- dual_price_vf: retention 90.2%, latency 16.997 us/decision
- rollout_teacher: retention 100.0%, latency 48.03 ms
- surrogate_linear: retention 91.1%, latency 74.760 us/decision
- paired vf-surrogate: -0.9 pp [CI95 -3.1, +1.4]; $-9,625 [CI95 -31,736, +13,376]
- Wilcoxon p = 0.329; sign test 12/30 wins, p = 0.362

### tight (n = 30 pairs)
- bid_price: retention 91.1%, latency 1.256 us/decision
- dual_price: retention 91.2%, latency 22.704 us/decision
- dual_price_vf: retention 95.4%, latency 23.421 us/decision
- rollout_teacher: retention 100.0%, latency 74.45 ms
- surrogate_linear: retention 93.4%, latency 80.704 us/decision
- paired vf-surrogate: +2.1 pp [CI95 +0.5, +3.7]; $+25,095 [CI95 +6,072, +43,794]
- Wilcoxon p = 0.019; sign test 19/30 wins, p = 0.200

## Table 2 inputs: certificates

### tight (10 instances)
- dual_price_vf: certified >= 60.1% of hindsight optimum (57.0--63.3)
- rollout_teacher: certified >= 62.8% of hindsight optimum (60.5--66.8)
- mean bound-solve time: 118 minutes

### scarce (10 instances)
- dual_price_vf: certified >= 57.7% of hindsight optimum (53.5--61.5)
- rollout_teacher: certified >= 63.7% of hindsight optimum (61.2--65.3)
- mean bound-solve time: 141 minutes

## Table 3 inputs: proportional scaling (tight, pair 0)
- tight_x05 (K=35): bound/K $26,780, policy/K $17,242, policy vs rollout 116.6%, certified gap 35.6%
- tight_x1 (K=70): bound/K $26,929, policy/K $16,970, policy vs rollout 93.3%, certified gap 37.0%
- tight_x2 (K=140): bound/K $31,585, policy/K $15,104, policy vs rollout 96.9%, certified gap 52.2%
