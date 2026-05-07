# Adding A Policy

FreightBidBench policies currently plug into
`scripts/run_surrogate_cascade.py`.

## Minimal Steps

1. Add the policy name to `policies.default` in
   `configs/freightbidbench_v02_scenarios.json` if it should appear in public
   benchmark runs. Bump `policy_set_version` when changing the public set.
2. Add a branch to `choose_action()` in `scripts/run_surrogate_cascade.py`.
3. Return:

   ```python
   return wants_accept, score, stage_name
   ```

   where `wants_accept` is a boolean, `score` is a decision score in dollars or
   dollar-like units, and `stage_name` is used for stage-share metrics.

4. Do not mutate `load` or `fleet` inside `choose_action()`. Fleet mutation
   happens only after the benchmark applies the accept/reject decision.
5. Run:

   ```bash
   make test
   python3 scripts/run_freightbidbench.py \
     --preset smoke \
     --label-limit 20 \
     --eval-load-limit 50 \
     --output-dir benchmark_runs/policy_smoke
   ```

## Policy Contract

A policy can read:

- candidate load fields,
- current fleet state,
- public-calibrated lane table,
- scenario configuration,
- state future-value features,
- optional trained surrogate model.

A policy must not depend on hidden future loads except through explicit rollout
calls. If a policy uses rollout, its decisions should be counted with the
`rollout` stage so latency/frontier metrics remain comparable.
