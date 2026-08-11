# Latency provenance for the headline table

Profits are deterministic given seeds; latencies are host-dependent.

| Rows | Host | Notes |
| --- | --- | --- |
| bid_price, surrogate_linear, rollout_teacher (all scenarios) | 4-core cloud VM (Ubuntu, Python 3.10) | original 30-seed program |
| cascade (benchmark_runs/trackb/cascade30) | 4-core cloud VM | Track B program |
| dual_price, dual_price_vf (rerun after the value-fitter correction) | Apple M-series laptop (macOS, Python 3.14) | see git history |
| dlp_resolve, all cadences (benchmark_runs/trackb/dlp30*) | Apple M-series laptop | per-directory manifest.json records platform/python |
| dual_price_vf_naive (benchmark_runs/trackb/naive30) | Apple M-series laptop | |

Cross-policy latency ratios that span the two hosts are indicative
only. Profit columns are unaffected by host.
