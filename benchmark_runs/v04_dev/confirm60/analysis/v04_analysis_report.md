# v0.4 analysis (regenerated from raw CSVs)

## Table 1 inputs: methods comparison

### mild (n = 30 pairs)
- bid_price: retention 98.0%, latency 1.301 us/decision
- dual_price: retention 98.2%, latency 93.634 us/decision
- dual_price_vf: retention 100.7%, latency 93.926 us/decision
- rollout_teacher: retention 100.0%, latency 116.65 ms
- surrogate_linear: retention 97.3%, latency 107.921 us/decision
- paired vf-surrogate: +3.4 pp [CI95 +2.3, +4.5]; $+47,025 [CI95 +31,839, +62,694]
- Wilcoxon p = 0.000; sign test 25/28 wins, p = 0.000

### scarce (n = 30 pairs)
- bid_price: retention 87.3%, latency 1.256 us/decision
- dual_price: retention 88.2%, latency 40.339 us/decision
- dual_price_vf: retention 91.0%, latency 40.707 us/decision
- rollout_teacher: retention 100.0%, latency 48.61 ms
- surrogate_linear: retention 87.9%, latency 76.149 us/decision
- paired vf-surrogate: +3.1 pp [CI95 -0.7, +8.3]; $+32,191 [CI95 -6,522, +85,734]
- Wilcoxon p = 0.658; sign test 16/30 wins, p = 0.856

### tight (n = 30 pairs)
- bid_price: retention 90.3%, latency 1.253 us/decision
- dual_price: retention 90.5%, latency 59.137 us/decision
- dual_price_vf: retention 94.1%, latency 59.995 us/decision
- rollout_teacher: retention 100.0%, latency 76.83 ms
- surrogate_linear: retention 93.5%, latency 85.850 us/decision
- paired vf-surrogate: +0.6 pp [CI95 -0.9, +2.0]; $+6,730 [CI95 -11,252, +25,022]
- Wilcoxon p = 0.544; sign test 16/30 wins, p = 0.856

## Table 2 inputs: certificates

### tight (10 instances)
- mean bound-solve time: 1019 minutes

### scarce (10 instances)
- mean bound-solve time: 1177 minutes

## Table 3 inputs: proportional scaling (tight, pair 0)
- tight_x05 (K=35): bound/K $26,780, policy/K $17,242, policy vs rollout 116.6%, certified gap 35.6%
- tight_x1 (K=70): bound/K $26,929, policy/K $16,970, policy vs rollout 93.3%, certified gap 37.0%
- tight_x2 (K=140): bound/K $31,585, policy/K $15,104, policy vs rollout 96.9%, certified gap 52.2%
