#!/usr/bin/env python3
"""Run FreightBidBench v0.2.

FreightBidBench is a public-calibrated synthetic benchmark for real-time
truckload bid acceptance. The benchmark intentionally has no third-party Python
dependencies: it uses the processed FAF/USDA seed lane table and the same
closed-loop simulator used in the research probes.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[0]
sys.path.insert(0, str(SCRIPT_DIR))

import run_closed_loop_baselines as base  # noqa: E402
import run_experimental_package as exp  # noqa: E402
import freight_feasibility as feas  # noqa: E402
import run_surrogate_cascade as sc  # noqa: E402


DEFAULT_CONFIG_PATH = ROOT / "configs" / "freightbidbench_v02_scenarios.json"
CONFIG_PATH = DEFAULT_CONFIG_PATH
BENCHMARK_CONFIG: dict[str, object] = {}
BENCHMARK_VERSION = ""
SCENARIO_CONFIG_VERSION = ""
POLICY_SET_VERSION = ""
DEFAULT_OUTPUT_DIR = ROOT / "benchmark_runs" / "current"
DEFAULT_FIRST_SEED = 0
CASCADE_POLICY = ""


def scenario_from_config(config: dict[str, object]) -> base.Scenario:
    return base.Scenario(
        str(config["name"]),
        horizon_hours=int(config["horizon_hours"]),
        loads_per_hour=int(config["loads_per_hour"]),
        fleet_size=int(config["fleet_size"]),
        base_cost_per_mile=float(config["base_cost_per_mile"]),
        fixed_load_cost=float(config["fixed_load_cost"]),
        value_scale_dollars=float(config["value_scale_dollars"]),
        service_failure_penalty_dollars=config.get("service_failure_penalty_dollars"),
        terminal_value_weight=config.get("terminal_value_weight"),
        demand_wave_schedule=config.get("demand_wave_schedule"),
    )


SCENARIO_CONFIGS: dict[str, dict[str, object]] = {}
SCENARIOS: dict[str, base.Scenario] = {}
PRESETS: dict[str, dict[str, object]] = {}
POLICIES: list[str] = []
EVALUATED_POLICIES: list[str] = []
DEFAULT_CASCADE_BANDS: list[float] = []
REPRESENTATIVE_CASCADE_BAND = 0.0


def load_benchmark_config(config_path: Path) -> dict[str, object]:
    path = config_path if config_path.is_absolute() else ROOT / config_path
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def apply_benchmark_config(config_path: Path) -> None:
    global CONFIG_PATH
    global BENCHMARK_CONFIG
    global BENCHMARK_VERSION
    global SCENARIO_CONFIG_VERSION
    global POLICY_SET_VERSION
    global DEFAULT_FIRST_SEED
    global CASCADE_POLICY
    global SCENARIO_CONFIGS
    global SCENARIOS
    global PRESETS
    global POLICIES
    global EVALUATED_POLICIES
    global DEFAULT_CASCADE_BANDS
    global REPRESENTATIVE_CASCADE_BAND

    path = config_path if config_path.is_absolute() else ROOT / config_path
    config = load_benchmark_config(path)
    scenario_configs = {
        str(name): dict(scenario_config)
        for name, scenario_config in dict(config["scenarios"]).items()
    }
    policies_config = dict(config["policies"])

    CONFIG_PATH = path
    BENCHMARK_CONFIG = config
    BENCHMARK_VERSION = str(config["benchmark_version"])
    SCENARIO_CONFIG_VERSION = str(config["scenario_config_version"])
    POLICY_SET_VERSION = str(config["policy_set_version"])
    DEFAULT_FIRST_SEED = int(config["default_first_seed"])
    CASCADE_POLICY = str(policies_config["cascade"])
    SCENARIO_CONFIGS = scenario_configs
    SCENARIOS = {
        name: scenario_from_config(scenario_config)
        for name, scenario_config in scenario_configs.items()
    }
    PRESETS = {
        str(name): dict(preset_config)
        for name, preset_config in dict(config["presets"]).items()
    }
    POLICIES = [str(policy) for policy in policies_config["default"]]
    EVALUATED_POLICIES = POLICIES + [CASCADE_POLICY]
    DEFAULT_CASCADE_BANDS = [
        float(band) for band in config["cascade_bands_dollars"]
    ]
    REPRESENTATIVE_CASCADE_BAND = float(
        config["representative_cascade_band_dollars"]
    )


apply_benchmark_config(DEFAULT_CONFIG_PATH)


def relative(path: Path) -> str:
    path = path.resolve()
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def parse_csv_names(value: str) -> list[str]:
    names = [item.strip() for item in value.split(",") if item.strip()]
    unknown = sorted(set(names) - set(SCENARIOS))
    if unknown:
        raise argparse.ArgumentTypeError(
            f"unknown scenario(s): {', '.join(unknown)}; choose from {', '.join(SCENARIOS)}"
        )
    return names


def parse_bands(value: str) -> list[float]:
    try:
        bands = [float(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("cascade bands must be comma-separated numbers") from exc
    if not bands:
        raise argparse.ArgumentTypeError("at least one cascade band is required")
    if any(band < 0 for band in bands):
        raise argparse.ArgumentTypeError("cascade bands must be non-negative")
    return sorted(bands)


def seed_pairs_from_count(seed_count: int, first_seed: int) -> list[tuple[int, int]]:
    if seed_count <= 0:
        raise ValueError("seed_count must be positive")
    return [(first_seed + 2 * idx, first_seed + 2 * idx + 1) for idx in range(seed_count)]


def output_paths(output_dir: Path) -> dict[str, Path]:
    return {
        "policy_runs": output_dir / "freightbidbench_policy_runs.csv",
        "static_fit": output_dir / "freightbidbench_static_label_fit.csv",
        "policy_summary": output_dir / "freightbidbench_policy_summary.csv",
        "frontier_summary": output_dir / "freightbidbench_frontier_summary.csv",
        "manifest": output_dir / "freightbidbench_manifest.json",
        "report": output_dir / "freightbidbench_report.md",
    }


def run_cell(
    lanes: list[dict[str, str]],
    scenario: base.Scenario,
    train_seed: int,
    eval_seed: int,
    cascade_bands: list[float],
    label_limit: int,
    eval_load_limit: int | None,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    start = time.perf_counter()
    state_values = base.build_state_values(lanes, scenario)

    previous_label_limit = sc.LABEL_DECISION_LIMIT
    sc.LABEL_DECISION_LIMIT = label_limit
    try:
        train_labels, _, _ = sc.generate_rollout_labels(
            lanes, scenario, train_seed, state_values
        )
        eval_labels, _, _ = sc.generate_rollout_labels(
            lanes, scenario, eval_seed, state_values
        )
    finally:
        sc.LABEL_DECISION_LIMIT = previous_label_limit
    model = sc.train_linear_model(train_labels)
    static_metrics = sc.evaluate_static_labels(model, eval_labels)

    eval_loads = sc.generate_loads_with_seed(lanes, scenario, eval_seed)
    if eval_load_limit is not None:
        eval_loads = eval_loads[:eval_load_limit]
    starting_fleet = sc.initial_fleet_with_seed(lanes, scenario, eval_seed)

    policy_summaries: dict[str, dict[str, object]] = {}
    for policy_name in POLICIES:
        summary, _ = sc.simulate_policy(
            policy_name,
            eval_loads,
            starting_fleet,
            lanes,
            scenario,
            state_values,
            model,
            rollout_seed_offset=eval_seed,
        )
        policy_summaries[policy_name] = summary

    rollout_profit = exp.as_float(policy_summaries["rollout_teacher"]["profit"])
    policy_rows = [
        exp.decorate_policy_row(
            summary,
            scenario,
            train_seed,
            eval_seed,
            rollout_profit,
            static_metrics,
            len(train_labels),
            len(eval_labels),
            time.perf_counter() - start,
        )
        for summary in policy_summaries.values()
    ]

    for band in cascade_bands:
        summary, _ = sc.simulate_policy(
            "cascade_surrogate_rollout",
            eval_loads,
            starting_fleet,
            lanes,
            scenario,
            state_values,
            model,
            cascade_band_dollars=band,
            rollout_seed_offset=eval_seed,
        )
        policy_rows.append(
            exp.decorate_policy_row(
                summary,
                scenario,
                train_seed,
                eval_seed,
                rollout_profit,
                static_metrics,
                len(train_labels),
                len(eval_labels),
                time.perf_counter() - start,
            )
        )

    fit_row = exp.static_fit_row(
        scenario,
        train_seed,
        eval_seed,
        static_metrics,
        len(train_labels),
        len(eval_labels),
        time.perf_counter() - start,
    )
    return policy_rows, fit_row


def representative_rows(
    policy_summary_rows: list[dict[str, object]],
    representative_band: float,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in policy_summary_rows:
        if row["policy"] != "cascade_surrogate_rollout":
            rows.append(row)
            continue
        if abs(exp.as_float(row["cascade_band_dollars"]) - representative_band) < 1e-9:
            rows.append(row)
    return sorted(rows, key=exp.aggregate_sort_key)


def scenario_manifest_row(name: str, scenario: base.Scenario) -> dict[str, object]:
    row = exp.scenario_config_row(scenario)
    raw_config = SCENARIO_CONFIGS.get(name, {})
    for key in [
        "service_failure_penalty_dollars",
        "terminal_value_weight",
        "demand_wave_schedule",
    ]:
        if key in raw_config:
            row[key] = raw_config[key]
    return row


def write_report(
    paths: dict[str, Path],
    scenario_names: list[str],
    scenarios: list[base.Scenario],
    seed_pairs: list[tuple[int, int]],
    cascade_bands: list[float],
    policy_summary_rows: list[dict[str, object]],
    frontier_rows: list[dict[str, object]],
    static_summary_rows: list[dict[str, object]],
    elapsed_seconds: float,
    preset: str,
    label_limit: int,
    eval_load_limit: int | None,
) -> None:
    seed_text = ", ".join(f"{train}/{eval_}" for train, eval_ in seed_pairs)
    feasibility_features = feas.enabled_feature_names()
    disabled_features = feas.config_to_dict()["disabled_features"]
    feasibility_text = (
        ", ".join(feasibility_features)
        if feasibility_features
        else "no operational feasibility features"
    )
    ablation_text = (
        ", ".join(f"`{feature}`" for feature in disabled_features)
        if disabled_features
        else "none"
    )
    scenario_lines = [
        "| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, scenario in zip(scenario_names, scenarios):
        scenario_lines.append(
            f"| `{name}` | `{scenario.name}` | {scenario.horizon_hours}h | "
            f"{scenario.loads_per_hour} | {scenario.fleet_size} | "
            f"${scenario.base_cost_per_mile:.2f} | ${scenario.value_scale_dollars:,.0f} |"
        )

    static_lines = [
        "| Scenario | Runs | Agreement | MAE | p90 Abs Error |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in static_summary_rows:
        static_lines.append(
            f"| `{row['scenario']}` | {row['n_runs']} | "
            f"{exp.percent(row['mean_agreement'])} | {exp.money(row['mean_mae'])} | "
            f"{exp.money(row['mean_p90_abs_error'])} |"
        )

    show_service_failure_cost = any(
        "mean_service_failure_penalty_cost" in row for row in policy_summary_rows
    )
    show_terminal_value = any(
        "mean_terminal_fleet_value" in row for row in policy_summary_rows
    )
    if show_service_failure_cost or show_terminal_value:
        policy_lines = [
            "| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    else:
        policy_lines = [
            "| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | HOS Rest h | Yard Delay h |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    for row in representative_rows(policy_summary_rows, REPRESENTATIVE_CASCADE_BAND):
        band = row["cascade_band_dollars"] or "-"
        policy_line = (
            f"| `{row['scenario']}` | `{row['policy']}` | {band} | "
            f"{exp.money(row['mean_profit'])} | +/- {exp.money(row['ci95_profit_halfwidth'])} | "
            f"{exp.percent(row['mean_profit_retention_vs_rollout'])} | "
            f"{exp.as_float(row['mean_latency_ms']):.3f} | "
            f"{exp.percent(row['mean_rollout_stage_share'])} | "
            f"{exp.as_float(row.get('mean_infeasible', 0)):.1f} | "
        )
        if show_service_failure_cost:
            policy_line += f"{exp.money(row.get('mean_service_failure_penalty_cost', 0))} | "
        if show_terminal_value:
            policy_line += f"{exp.money(row.get('mean_terminal_fleet_value', 0))} | "
        policy_line += (
            f"{exp.as_float(row.get('mean_hos_rest_hours', 0)):,.0f} | "
            f"{exp.as_float(row.get('mean_yard_delay_hours', 0)):,.0f} |"
        )
        policy_lines.append(policy_line)

    frontier_lines = [
        "| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in frontier_rows:
        frontier_lines.append(
            f"| `{row['scenario']}` | {exp.as_float(row['cascade_band_dollars']):,.0f} | "
            f"{exp.percent(row['mean_profit_retention_vs_rollout'])} | "
            f"{exp.money(row['mean_profit'])} | {exp.as_float(row['mean_latency_ms']):.3f} | "
            f"{exp.percent(row['mean_rollout_stage_share'])} |"
        )

    artifact_lines = "\n".join(
        f"- `{relative(path)}`" for key, path in paths.items() if key != "report"
    )

    content = f"""# FreightBidBench Report

## Configuration

- Benchmark version: `{BENCHMARK_VERSION}`
- Scenario config: `{relative(CONFIG_PATH)}`
- Preset: `{preset}` ({PRESETS[preset]['description']})
- Seed pairs: {seed_text}
- Policies: {", ".join(f"`{policy}`" for policy in EVALUATED_POLICIES)}
- Cascade bands: {", ".join(f"+/- ${band:,.0f}" for band in cascade_bands)}
- Rollout labels per train/eval stream: up to {label_limit:,}
- Evaluation load limit: {eval_load_limit if eval_load_limit is not None else "full horizon"}
- Feasibility layer: {feasibility_text}
- Disabled feasibility features: {ablation_text}
- Total runtime: {elapsed_seconds:.2f} seconds

{chr(10).join(scenario_lines)}

## Offline Label Fit

{chr(10).join(static_lines)}

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- ${REPRESENTATIVE_CASCADE_BAND:,.0f} escalation band.

{chr(10).join(policy_lines)}

## Cascade Frontier

{chr(10).join(frontier_lines)}

## Output Files

{artifact_lines}

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
"""
    paths["report"].write_text(content, encoding="utf-8")


def write_manifest(
    paths: dict[str, Path],
    preset: str,
    scenario_names: list[str],
    scenarios: list[base.Scenario],
    seed_pairs: list[tuple[int, int]],
    cascade_bands: list[float],
    label_limit: int,
    eval_load_limit: int | None,
    elapsed_seconds: float,
    row_counts: dict[str, int],
) -> None:
    manifest = {
        "benchmark_version": BENCHMARK_VERSION,
        "scenario_config_version": SCENARIO_CONFIG_VERSION,
        "policy_set_version": POLICY_SET_VERSION,
        "scenario_config_path": relative(CONFIG_PATH),
        "preset": preset,
        "preset_description": PRESETS[preset]["description"],
        "command": " ".join(sys.argv),
        "python": sys.version.split()[0],
        "elapsed_seconds": round(elapsed_seconds, 2),
        "source_inputs": {
            "lane_table": relative(base.LANES),
            "state_imbalance_table": relative(base.IMBALANCE),
        },
        "seed_pairs": [
            {"train_seed": train_seed, "eval_seed": eval_seed}
            for train_seed, eval_seed in seed_pairs
        ],
        "policies": POLICIES,
        "cascade_policy": CASCADE_POLICY,
        "evaluated_policies": EVALUATED_POLICIES,
        "cascade_bands_dollars": cascade_bands,
        "label_limit": label_limit,
        "eval_load_limit": eval_load_limit,
        "feasibility_layer": {
            "individual_truck_state": True,
            **feas.config_to_dict(),
        },
        "scenarios": {
            name: scenario_manifest_row(name, scenario)
            for name, scenario in zip(scenario_names, scenarios)
        },
        "outputs": {key: relative(path) for key, path in paths.items()},
        "row_counts": row_counts,
        "notes": [
            "Synthetic load arrivals are calibrated from public FAF/USDA-derived processed inputs.",
            "Rollout teacher is finite-lookahead and stochastic; it is not an oracle.",
            "Latency is measured inside this Python reference implementation.",
        ],
    }
    paths["manifest"].write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run FreightBidBench, a public-calibrated truckload bid benchmark."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Benchmark scenario config JSON. Defaults to the v0.2 release contract.",
    )
    parser.add_argument(
        "--preset",
        default="standard",
        help="Benchmark preset. Use paper for a stronger multi-seed run.",
    )
    parser.add_argument(
        "--scenarios",
        help="Comma-separated scenario subset. Overrides the preset scenario list.",
    )
    parser.add_argument(
        "--seed-count",
        type=int,
        help="Number of train/eval seed pairs. Overrides the preset seed count.",
    )
    parser.add_argument(
        "--first-seed",
        type=int,
        help="First train seed; eval seeds are generated as train_seed + 1.",
    )
    parser.add_argument(
        "--label-limit",
        type=int,
        help="Rollout-label decisions per train/eval stream. Overrides the preset label limit.",
    )
    parser.add_argument(
        "--eval-load-limit",
        type=int,
        help="Limit evaluated online loads per scenario/seed. Defaults to preset value.",
    )
    parser.add_argument(
        "--cascade-bands",
        type=parse_bands,
        help="Comma-separated cascade escalation bands in dollars.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for benchmark CSV, manifest, and report outputs.",
    )
    parser.add_argument(
        "--disable-pickup-reach",
        action="store_true",
        help="Ablation: remove origin-market pickup deadhead time and cost.",
    )
    parser.add_argument(
        "--disable-time-windows",
        action="store_true",
        help="Ablation: do not enforce pickup and delivery appointment windows.",
    )
    parser.add_argument(
        "--disable-hos",
        action="store_true",
        help="Ablation: do not enforce simplified 11/14/10 HOS clocks.",
    )
    parser.add_argument(
        "--disable-yard-delays",
        action="store_true",
        help="Ablation: remove stochastic pickup/dropoff yard delays and delay cost.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    apply_benchmark_config(args.config)
    if args.preset not in PRESETS:
        raise SystemExit(
            f"--preset must be one of: {', '.join(sorted(PRESETS))}"
        )
    feas.set_config(
        feas.config_from_disabled(
            disable_pickup_reach=args.disable_pickup_reach,
            disable_time_windows=args.disable_time_windows,
            disable_hos=args.disable_hos,
            disable_yard_delays=args.disable_yard_delays,
        )
    )
    seed_count = (
        args.seed_count
        if args.seed_count is not None
        else int(PRESETS[args.preset]["seed_count"])
    )
    if seed_count <= 0:
        raise SystemExit("--seed-count must be positive")
    label_limit = (
        args.label_limit
        if args.label_limit is not None
        else int(PRESETS[args.preset]["label_limit"])
    )
    if label_limit <= 0:
        raise SystemExit("--label-limit must be positive")
    eval_load_limit = (
        args.eval_load_limit
        if args.eval_load_limit is not None
        else PRESETS[args.preset]["eval_load_limit"]
    )
    if eval_load_limit is not None and eval_load_limit <= 0:
        raise SystemExit("--eval-load-limit must be positive")

    first_seed = args.first_seed if args.first_seed is not None else DEFAULT_FIRST_SEED
    scenario_names = (
        parse_csv_names(args.scenarios)
        if args.scenarios
        else list(PRESETS[args.preset]["scenarios"])
    )
    scenarios = [SCENARIOS[name] for name in scenario_names]
    seed_pairs = seed_pairs_from_count(seed_count, first_seed)
    cascade_bands = args.cascade_bands or list(DEFAULT_CASCADE_BANDS)
    paths = output_paths(args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    start = time.perf_counter()
    lanes = base.load_csv(base.LANES)
    policy_rows: list[dict[str, object]] = []
    static_rows: list[dict[str, object]] = []

    for scenario_name, scenario in zip(scenario_names, scenarios):
        for train_seed, eval_seed in seed_pairs:
            print(
                f"Running {scenario_name} train_seed={train_seed} eval_seed={eval_seed}",
                flush=True,
            )
            cell_policy_rows, cell_static_row = run_cell(
                lanes,
                scenario,
                train_seed,
                eval_seed,
                cascade_bands,
                label_limit,
                eval_load_limit,
            )
            policy_rows.extend(cell_policy_rows)
            static_rows.append(cell_static_row)

    policy_summary_rows = exp.aggregate_policy_rows(policy_rows)
    static_summary_rows = exp.aggregate_static_rows(static_rows)
    frontier_rows = exp.build_frontier_rows(policy_summary_rows)
    elapsed_seconds = time.perf_counter() - start

    sc.write_csv(paths["policy_runs"], policy_rows)
    sc.write_csv(paths["static_fit"], static_rows)
    sc.write_csv(paths["policy_summary"], policy_summary_rows)
    sc.write_csv(paths["frontier_summary"], frontier_rows)
    write_report(
        paths,
        scenario_names,
        scenarios,
        seed_pairs,
        cascade_bands,
        policy_summary_rows,
        frontier_rows,
        static_summary_rows,
        elapsed_seconds,
        args.preset,
        label_limit,
        eval_load_limit,
    )
    write_manifest(
        paths,
        args.preset,
        scenario_names,
        scenarios,
        seed_pairs,
        cascade_bands,
        label_limit,
        eval_load_limit,
        elapsed_seconds,
        {
            "policy_runs": len(policy_rows),
            "static_fit": len(static_rows),
            "policy_summary": len(policy_summary_rows),
            "frontier_summary": len(frontier_rows),
        },
    )

    print(f"Wrote {relative(paths['report'])}")
    for row in representative_rows(policy_summary_rows, REPRESENTATIVE_CASCADE_BAND):
        print(
            f"{row['scenario']} {row['policy']} band={row['cascade_band_dollars'] or '-'}: "
            f"mean profit {exp.money(row['mean_profit'])}, "
            f"retention {exp.percent(row['mean_profit_retention_vs_rollout'])}, "
            f"mean latency {exp.as_float(row['mean_latency_ms']):.3f} ms"
        )


if __name__ == "__main__":
    main()
