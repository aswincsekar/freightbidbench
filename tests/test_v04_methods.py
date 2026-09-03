"""v0.4 methods coverage: kernel certificates, bound validity at micro
scale, permissive snapping, dual-price fitting, value-to-go recursion,
and the paper-number regeneration pipeline."""

import random
import unittest
from fractions import Fraction
from pathlib import Path
from unittest import mock

from scripts import fit_dual_prices
from scripts import fit_value_togo
from scripts import find_gap_kernel as kern
from scripts import freight_feasibility as feas
from scripts import run_hindsight_bound as hb
from scripts import run_lagrangian_bound as lag
from tests.test_hindsight_bound import make_load

REPO = Path(__file__).resolve().parent.parent

K1_TRUCKS = (
    kern.Truck(0, 1, 1, 2),
    kern.Truck(1, 2, 0, 2),
    kern.Truck(2, 0, 1, 2),
)
K1_LOADS = (
    kern.Load(0, 0, 1, 2, 1, 6),
    kern.Load(1, 1, 0, 1, 2, 13),
    kern.Load(2, 1, 2, 0, 2, 6),
    kern.Load(3, 4, 0, 2, 1, 14),
    kern.Load(4, 4, 1, 0, 1, 7),
    kern.Load(5, 5, 2, 1, 1, 14),
)
K1_LAMBDA = [
    Fraction(0),
    Fraction(0),
    Fraction(0),
    Fraction(21, 2),
    Fraction(7),
    Fraction(9, 2),
]
K1_MU = [Fraction(0), Fraction(19, 2), Fraction(13)]


class KernelCertificateTests(unittest.TestCase):
    def test_k1_integer_optimum_is_41(self):
        self.assertEqual(kern.joint_optimum(K1_TRUCKS, K1_LOADS), 41)

    def test_k1_lp_value_is_89_halves(self):
        value, _ = kern.chain_packing_lp(K1_TRUCKS, K1_LOADS)
        self.assertEqual(value, Fraction(89, 2))

    def test_k1_dual_certificate_feasible_and_matching(self):
        # The paper's Check 4: dual feasibility over every enumerated
        # chain, and dual value equal to the primal packing's 89/2.
        chains = [
            (tr.truck_id, loadset, value)
            for tr in K1_TRUCKS
            for loadset, value in kern.truck_chains(tr, K1_LOADS)
        ]
        self.assertEqual(len(chains), 8)
        for truck_id, loadset, value in chains:
            lhs = K1_MU[truck_id] + sum(K1_LAMBDA[t] for t in loadset)
            self.assertGreaterEqual(lhs, value)
        self.assertEqual(sum(K1_LAMBDA) + sum(K1_MU), Fraction(89, 2))


class MicroBoundValidityTests(unittest.TestCase):
    def test_chain_lp_upper_bounds_exact_optimum(self):
        # Weak duality at micro scale, in exact rationals: the
        # chain-packing LP (= min_lambda L by Dantzig-Wolfe) can never
        # fall below the enumerated joint optimum.
        rng = random.Random(7)
        for _ in range(25):
            trucks, loads = kern.sample_instance(rng)
            v_star = kern.joint_optimum(trucks, loads)
            lp_value, _ = kern.chain_packing_lp(trucks, loads)
            self.assertGreaterEqual(lp_value, Fraction(v_star))


class SnappingTests(unittest.TestCase):
    def test_snapping_is_permissive_on_every_clock(self):
        state = lag.TruckDPState(
            location="GA",
            available_time=3.37,
            drive_used=5.9,
            duty_used=7.49,
            value=123.0,
        )
        _, snapped = lag.bucket_key_and_snapped(state)
        self.assertLessEqual(snapped.available_time, state.available_time)
        self.assertLessEqual(snapped.drive_used, state.drive_used)
        self.assertLessEqual(snapped.duty_used, state.duty_used)
        self.assertEqual(snapped.value, state.value)

    def test_bucket_edges_snap_to_themselves(self):
        state = lag.TruckDPState(
            location="GA",
            available_time=0.5,
            drive_used=2.0,
            duty_used=3.0,
            value=0.0,
        )
        _, snapped = lag.bucket_key_and_snapped(state)
        self.assertAlmostEqual(snapped.available_time, 0.5)
        self.assertAlmostEqual(snapped.drive_used, 2.0)
        self.assertAlmostEqual(snapped.duty_used, 3.0)


class SnappedBoundIntegrationTests(unittest.TestCase):
    """Validity of the actual bucket-snapped Lagrangian solver on a
    complete micro instance: for any duals, L(lambda) upper-bounds the
    joint optimum, hence also the exact fixed-dispatch hindsight value
    (a necessary condition; the fixed-dispatch DP is a lower bound on
    the joint V*)."""

    def tearDown(self):
        feas.reset_config()

    def _instance(self):
        loads = [
            make_load(1, 0.0, "A", "B", 300.0, linehaul_hours=3.0),
            make_load(2, 1.0, "A", "C", 500.0, linehaul_hours=1.0),
            make_load(3, 2.0, "C", "A", 250.0, linehaul_hours=2.0),
            make_load(4, 6.0, "B", "A", 400.0, linehaul_hours=2.0),
        ]
        # Both bound scripts do a bare `import freight_feasibility`
        # (scripts/ on sys.path), which is a distinct module object
        # from tests' `scripts.freight_feasibility`; isinstance checks
        # inside them require constructing trucks from their module.
        truck_state = lag.feas.TruckState
        fleet = {
            "A": [
                truck_state("t1", "A", 0.0),
                truck_state("t2", "A", 0.0),
            ]
        }
        return loads, fleet

    def test_snapped_lagrangian_upper_bounds_exact_hindsight(self):
        loads, fleet = self._instance()
        exact_solution = hb.exact_hindsight_bound(loads, fleet, None, {})
        self.assertGreater(exact_solution.profit, 0.0)
        for duals in (
            {},
            {1: 50.0, 2: 100.0, 3: 10.0, 4: 25.0},
            {1: 500.0, 2: 500.0, 3: 500.0, 4: 500.0},
        ):
            evaluation = lag.evaluate_lagrangian(fleet, loads, duals, 0.0, {})
            self.assertGreaterEqual(
                evaluation.bound + 1e-9, exact_solution.profit
            )

    def test_subgradient_loop_keeps_bound_valid(self):
        loads, fleet = self._instance()
        exact_solution = hb.exact_hindsight_bound(loads, fleet, None, {})
        _, best, _ = lag.subgradient_dual_loop(
            fleet, loads, 0.0, {}, iterations=5, step_scale=10.0
        )
        self.assertGreaterEqual(best.bound + 1e-9, exact_solution.profit)


class JointOptimumTests(unittest.TestCase):
    """The exact-vs-relaxation study's ordering invariants on a real
    micro instance: chain LP (= min L) >= joint optimum >= fixed-
    dispatch optimum, all on the same objective."""

    def tearDown(self):
        feas.reset_config()

    def test_ordering_on_micro_instance(self):
        import json

        from scripts import run_closed_loop_baselines as sbase
        from scripts import run_joint_optimum as jo

        with open(REPO / "configs/freightbidbench_v03_scenarios.json") as fh:
            config = json.load(fh)
        scenario = jo.lag.scenario_from_config(config["scenarios"]["tight"])
        lanes = sbase.load_csv(sbase.LANES)
        state_values = sbase.build_state_values(lanes, scenario)
        omega = sbase.terminal_value_weight(scenario)
        loads, placement = jo.micro_instance(lanes, scenario, 20260509, 4, 14)
        starts = [
            jo.lag.TruckDPState(m, a, 0.0, 0.0, 0.0) for m, a in placement
        ]
        fleet = {}
        for j, (m, a) in enumerate(placement):
            fleet.setdefault(m, []).append(jo.lag.feas.TruckState(f"t{j}", m, a))

        lp, integral, max_chain = jo.chain_packing_bound(
            starts, loads, omega, state_values
        )
        self.assertIsInstance(integral, bool)
        self.assertGreaterEqual(max_chain, 1)
        v_joint = jo.joint_optimum(starts, loads, omega, state_values)
        v_fixed = jo.fixed_dispatch_optimum(
            loads, fleet, scenario, state_values
        )
        self.assertGreaterEqual(lp + 1e-6, v_joint)
        self.assertGreaterEqual(v_joint + 1e-6, v_fixed)
        self.assertGreater(v_joint, 0.0)  # contended instance, not degenerate


class BoundValidityTests(unittest.TestCase):
    """The bucketed per-truck solver must upper-bound the exact
    one-truck optimum. Round 17: rounding HOS usage down is not
    permissive on its own (mandatory rests renew clocks). Round 18:
    the voluntary-rest corner rule is not sound either (value is not
    monotone in the state; counterexample below); the "sound" mode
    covers every state an entry stands for and needs no
    monotonicity (paper Appendix, frontier-coverage theorem)."""

    @classmethod
    def _stream(cls):
        import json
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        import run_closed_loop_baselines as rbase
        import run_lagrangian_bound as rlag
        import run_surrogate_cascade as rsc

        config = json.loads(
            (REPO / "configs/freightbidbench_v03_scenarios.json").read_text()
        )
        scenario = rlag.scenario_from_config(config["scenarios"]["tight"])
        lanes = rbase.load_csv(rbase.LANES)
        return rlag, rsc.generate_loads_with_seed(lanes, scenario, 20260509)

    def test_hos_reset_counterexample(self):
        """Loads 5, 481, 608 of the tight 20260509 stream: the exact
        one-truck plan takes all three via a clock-renewing reset; the
        pre-fix solver dropped load 5 and reported $5,174.83 against
        the exact $6,760.01."""
        from scripts import run_joint_optimum as jo

        rlag, stream = self._stream()
        loads = sorted(
            (l for l in stream if int(l["load_id"]) in (5, 481, 608)),
            key=lambda l: float(l["hour"]),
        )
        start = rlag.TruckDPState("48", 0.0, 0.0, 0.0, 0.0)
        best = rlag.solve_truck_sub_mdp(start, loads, {}, 0.0, {}, "t0")
        exact = jo.joint_optimum([start], loads, 0.0, {})
        self.assertGreaterEqual(best.value + 1e-6, exact)
        self.assertAlmostEqual(exact, 6760.01, places=2)

    def test_randomized_one_truck_upper_bound(self):
        """Random small one-truck instances: the sound bucketed solver
        at zero duals must never fall below the exact joint DP."""
        from scripts import run_joint_optimum as jo

        rlag, stream = self._stream()
        rng = random.Random(20260811)
        markets = sorted({str(l["origin_state"]) for l in stream})
        for trial in range(12):
            market = rng.choice(markets)
            local = [
                l for l in stream if str(l["origin_state"]) == market
            ]
            if len(local) < 4:
                continue
            picks = sorted(
                rng.sample(local, min(6, len(local))),
                key=lambda l: float(l["hour"]),
            )
            start = rlag.TruckDPState(market, 0.0, 0.0, 0.0, 0.0)
            best = rlag.solve_truck_sub_mdp(
                start, picks, {}, 0.0, {}, "t", mode="sound"
            )
            exact = jo.joint_optimum([start], picks, 0.0, {})
            # joint_optimum rounds each profit to integer cents
            # (round-half can go up); the solver sums raw floats, so
            # allow half a cent per load of comparison slack.
            self.assertGreaterEqual(
                best.value + 0.005 * len(picks) + 1e-6,
                exact,
                f"bound violation on trial {trial} market {market}",
            )

    # A one-load instance (found by randomized search, reviewer round
    # 18) on which the legacy corner rule -- the entry's own schedule
    # plus a voluntary rest before service -- certifies $0 while the
    # exact truck earns the load: the exact truck is forced to rest 1.5 h
    # into its deadhead and arrives fresh; the favorably snapped corner
    # skips that rest, waits 9.76 h for the window (no renewal), exhausts
    # during pickup service and misses delivery, and the rest-first
    # alternative lacks drive hours for the linehaul. No corner can
    # emulate a rest in the middle of a primitive.
    COUNTEREXAMPLE_START = ("A", 0.0008178248256458798, 3.8432410125233534, 12.51720296748509)
    COUNTEREXAMPLE_LOAD = {
        "load_id": 0, "hour": 2.9784573894100195, "origin_state": "A",
        "destination_state": "B", "price": 1000.0, "direct_cost": 0.0,
        "base_cost_per_mile": 0.0, "pickup_deadhead_miles": 61.559705351603974,
        "pickup_deadhead_hours": 1.6199922460948415,
        "pickup_earliest": 14.360950913917575, "pickup_latest": 20.907450941210932,
        "linehaul_drive_hours": 10.256203939309913, "travel_hours": 10.256203939309913,
        "delivery_earliest": 21.829483311881564, "delivery_latest": 35.19430066191626,
        "pickup_yard_delay_hours": 0.0, "dropoff_yard_delay_hours": 0.0,
    }

    def test_corner_rule_counterexample(self):
        from scripts import run_joint_optimum as jo

        rlag, _ = self._stream()
        start = rlag.TruckDPState(*self.COUNTEREXAMPLE_START, 0.0)
        loads = [dict(self.COUNTEREXAMPLE_LOAD)]
        exact = jo.joint_optimum([start], loads, 0.0, {})
        self.assertAlmostEqual(exact, 1000.0, places=6)
        corner = rlag.solve_truck_sub_mdp(start, loads, {}, 0.0, {}, "t", mode="corner")
        self.assertLess(corner.value, exact, "corner rule unexpectedly covers the instance")
        sound = rlag.solve_truck_sub_mdp(start, loads, {}, 0.0, {}, "t", mode="sound")
        self.assertGreaterEqual(sound.value + 1e-6, exact)

    def test_schedule_cover_covers_worse_states(self):
        """The coverage lemma's inductive step, mechanized: for a random
        frontier corner q and random states y at least as bad as q,
        every feasible schedule of y is at least as bad as some branch
        of schedule_cover(q)."""
        import freight_feasibility as feas

        rlag, stream = self._stream()
        rng = random.Random(20260901)
        checked = 0
        for _ in range(400):
            load = rng.choice(stream)
            hour = float(load["hour"])
            q_time = hour - rng.uniform(0, 6)
            q_drive = rng.uniform(0, feas.MAX_DRIVE_HOURS)
            q_duty = rng.uniform(q_drive, feas.MAX_DUTY_HOURS)
            q = feas.TruckState("q", str(load["origin_state"]), q_time, q_drive, q_duty)
            cover = rlag.schedule_cover(q, load, hour)
            for _ in range(8):
                y = feas.TruckState(
                    "y",
                    q.state,
                    q_time + rng.uniform(0, 12),
                    min(feas.MAX_DRIVE_HOURS, q_drive + rng.uniform(0, 3)),
                    min(feas.MAX_DUTY_HOURS, q_duty + rng.uniform(0, 3)),
                )
                if y.drive_used_hours > y.duty_used_hours:
                    continue
                sched = feas.plan_schedule(y, load, hour)
                if not sched.feasible:
                    continue
                checked += 1
                fy = (sched.final_available_time, sched.drive_used_hours, sched.duty_used_hours)
                self.assertTrue(
                    any(
                        b[0] <= fy[0] + 1e-9 and b[1] <= fy[1] + 1e-9 and b[2] <= fy[2] + 1e-9
                        for b in cover
                    ),
                    f"uncovered schedule {fy} for y={y} q={q} cover={cover}",
                )
        self.assertGreater(checked, 200)


class ScalingCrossfitAggregationTests(unittest.TestCase):
    def test_artifact_regenerates_from_run_directories(self):
        """The checked-in scaling_crossfit.csv must be reproducible
        from the 18 run directories alone (deterministic aggregation,
        explicit table provenance)."""
        import csv
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        import aggregate_scaling_crossfit as agg

        fresh = agg.aggregate(out_path=None)
        with (
            REPO / "benchmark_runs/trackb/scaling_crossfit"
            / "scaling_crossfit.csv"
        ).open() as handle:
            stored = list(csv.DictReader(handle))
        self.assertEqual(len(fresh), len(stored))
        for f, s in zip(fresh, stored):
            for col in ("cell", "table_train_seed", "eval_seed",
                        "profit", "rollout", "bound"):
                self.assertEqual(str(f[col]), s[col], col)


class MatchedFamilyDriverTests(unittest.TestCase):
    def test_shrinkage_matches_production_rule(self):
        """The family's fitter must apply the production fitter's
        five-pseudo-observation shrinkage: (sum + 5 * lane_mean) /
        (n + 5)."""
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        import run_matched_family as mf

        loads = [
            (0, "A", "B", 800.0),
            (1, "A", "B", 800.0),
            (1, "A", "B", 800.0),
        ]
        lam = [100.0, 40.0, 40.0]
        cell, lane, _ = mf.fit_tables(loads, lam, shrinkage=True)
        lane_mean = (100.0 + 40.0 + 40.0) / 3
        self.assertAlmostEqual(lane[("A", "B")], lane_mean)
        self.assertAlmostEqual(
            cell[("A", "B", 0)], (100.0 + 5 * lane_mean) / 6
        )
        self.assertAlmostEqual(
            cell[("A", "B", 1)], (80.0 + 5 * lane_mean) / 7
        )
        raw, _, _ = mf.fit_tables(loads, lam, shrinkage=False)
        self.assertAlmostEqual(raw[("A", "B", 0)], 100.0)


    def test_driver_reproduces_artifact_row(self):
        """Rerun the assumption-matched driver at its smallest cell and
        compare against the checked-in artifact (deterministic seeds:
        the row must regenerate exactly)."""
        import csv
        import subprocess
        import sys
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "mf.csv"
            subprocess.run(
                [
                    sys.executable,
                    str(REPO / "scripts/run_matched_family.py"),
                    "--fleet-sizes", "48",
                    "--pairs", "1",
                    "--output", str(out),
                ],
                check=True,
                capture_output=True,
            )
            with out.open() as handle:
                fresh = next(csv.DictReader(handle))
        with (
            REPO / "benchmark_runs/trackb/matched_family.csv"
        ).open() as handle:
            stored = next(
                r
                for r in csv.DictReader(handle)
                if r["fleet"] == "48" and r["pair"] == "0"
            )
        for col in ("certified_pct", "gap_per_truck", "bound", "profit"):
            self.assertEqual(fresh[col], stored[col], col)


class TrackbAnalysisTests(unittest.TestCase):
    def test_trackb_statistics_regenerate(self):
        import subprocess
        import sys

        out = subprocess.run(
            [sys.executable, str(REPO / "scripts/analyze_trackb_results.py")],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        # Micro attribution: both designs, with per-instance dispatch
        # share distributions (reviewer round 4).
        self.assertIn(
            "windowed ex-ante (primary), 30 instances: pooled"
            " slack/dispatch/accept = 0.3/12.0/87.7%;"
            " integral optimal solution on 26/30",
            out,
        )
        self.assertIn(
            "stream-prefix (legacy), 30 instances: pooled"
            " slack/dispatch/accept = 0.0/14.6/85.4%;"
            " integral optimal solution on 30/30",
            out,
        )
        self.assertIn("max 0.71 pp", out)
        self.assertIn("tight_x1: certified gap 41.2", out)
        # Cross-fitted scaling (deployment-valid Table 3 columns).
        self.assertIn(
            "tight_x05: vs rollout 103.9 +- 4.1%,"
            " certified gap 35.2 +- 1.3%",
            out,
        )
        # Out-of-sample cross-fit and honest guard diagnostics.
        self.assertIn(
            "sub_x2: certified 45.5 +- 1.1%"
            " (out of sample; by evaluation stream, n=3)",
            out,
        )
        self.assertIn("score-positive blocked", out)
        # DLP cadence sensitivity with consistent duration semantics
        # and corrected terminal accounting (reviewer rounds 5-6):
        # coarse cadence collapses; the training-tuned cadence (3 h
        # tight/mild, 6 h scarce) out-earns the dual policy on the
        # stress scenarios.
        self.assertIn("tight 12h: -18.48 pp", out)
        self.assertIn("tight  3h: +3.60 pp [CI95 +2.05, +5.09]", out)
        self.assertIn("tight  2h: +4.07 pp", out)
        self.assertIn("scarce  6h: +8.31 pp", out)
        self.assertIn("mild  1h: -7.28 pp", out)
        # Policy-agnostic certifier: the tuned DLP is itself certified.
        self.assertIn("tight: dlp 3h certified >= 62.7% (57.3--65.0)", out)
        self.assertIn("scarce: dlp 6h certified >= 61.0% (56.1--63.9)", out)
        # Bonferroni simultaneous CIs regenerate with the documented seed.
        self.assertIn("tight: +2.09 pp [+0.14, +4.01] excludes 0", out)
        # Assumption-matched family (30 train/eval pairs per size,
        # LP duals at numerical optimality, production shrinkage):
        # deterministic seeds, exact regeneration of both convergence
        # statements and the diagnostics.
        self.assertIn("K=   48: certified 70.16 +- 14.83%", out)
        self.assertIn("K=  384: certified 97.73 +- 6.96%", out)
        self.assertIn(
            "K=  768: certified 99.76 +- 1.30%, gap/truck $6.57,"
            " price RMSE $5, max W-err $10, no-block 29/30",
            out,
        )
        # The no-shrinkage sensitivity artifact regenerates through the
        # same analyzer path.
        self.assertIn("(sensitivity, no shrinkage)", out)
        self.assertIn("K=  768: certified 99.90 +- 0.55%, gap/truck $2.77", out)
        # Resolve-cost artifact is echoed (shape and provenance only;
        # timings are machine-specific).
        self.assertIn("x1: 74 lanes, 12 markets", out)
        self.assertIn("x8: 592 lanes, 96 markets", out)
        self.assertIn("dense two-phase simplex", out)


class ConfirmationAnalysisTests(unittest.TestCase):
    """The pre-registered confirmation statistics (pairs 31-60)
    regenerate exactly from the locked artifacts with the frozen
    estimators; these are the paper's headline numbers."""

    def test_confirmation_statistics_regenerate(self):
        import subprocess
        import sys

        out = subprocess.run(
            [sys.executable, str(REPO / "scripts/analyze_confirmation.py")],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        # Bonferroni-simultaneous 98.33% CIs: only mild excludes zero;
        # the development-set tight effect did not replicate.
        self.assertIn("tight: +0.57 pp [-1.22, +2.34] includes 0", out)
        self.assertIn("scarce: +3.10 pp [-1.35, +9.53] includes 0", out)
        self.assertIn("mild: +3.42 pp [+2.09, +4.75] excludes 0", out)
        # Tuned-cadence DLP ordering confirms: out-earns on the stress
        # scenarios, loses on mild.
        self.assertIn("delta +5.03 pp [CI95 +3.87, +6.24]", out)
        self.assertIn("delta +8.03 pp [CI95 +6.37, +9.64]", out)
        self.assertIn("delta -7.67 pp [CI95 -8.77, -6.54]", out)
        # Naive-continuation collapse replicates.
        self.assertIn("tight: 26.3% (sd 2.1)", out)
        self.assertIn("scarce: 29.6% (sd 2.4)", out)
        self.assertIn("mild: 23.9% (sd 2.0)", out)
        # Mild exceeds the rollout teacher on the confirmatory set.
        self.assertIn("mild: 100.7% (sd 2.4); beats rollout on 19/30", out)

    def test_frozen_analyzer_headline_numbers(self):
        import subprocess
        import sys

        out = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts/analyze_v04_results.py"),
                "--seed30-dir",
                str(REPO / "benchmark_runs/v04_dev/confirm60"),
                "--mild-dir",
                str(REPO / "benchmark_runs/v04_dev/confirm60/mild"),
                "--output-dir",
                str(REPO / "benchmark_runs/v04_dev/confirm60/analysis"),
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        self.assertIn(
            "paired vf-surrogate: +0.6 pp [CI95 -0.9, +2.0];"
            " $+6,730 [CI95 -11,252, +25,022]",
            out,
        )
        self.assertIn(
            "paired vf-surrogate: +3.1 pp [CI95 -0.7, +8.3];"
            " $+32,191 [CI95 -6,522, +85,734]",
            out,
        )
        self.assertIn(
            "paired vf-surrogate: +3.4 pp [CI95 +2.3, +4.5];"
            " $+47,025 [CI95 +31,839, +62,694]",
            out,
        )
        self.assertIn("Wilcoxon p = 0.544; sign test 16/30 wins", out)
        self.assertIn("sign test 25/28 wins", out)
        # Table 1 retention means (confirmation pairs).
        self.assertIn("dual_price_vf: retention 94.1%", out)
        self.assertIn("dual_price_vf: retention 91.0%", out)
        self.assertIn("dual_price_vf: retention 100.7%", out)


class DlpNetworkInvariantTests(unittest.TestCase):
    """Network-flow invariants of the stage DLP (reviewer round 6):
    terminal value is earned exactly once per truck, post-horizon
    trucks add no capacity, fractional durations bin by exact ceiling,
    and the decision score reads the actual completion time."""

    @staticmethod
    def _setup(horizon_hours, loads_per_hour=2.0):
        import run_closed_loop_baselines as rbase
        from scripts import run_dlp_resolve as dlp

        scenario = rbase.Scenario(
            name="dlp_invariant_micro",
            horizon_hours=horizon_hours,
            loads_per_hour=loads_per_hour,
            fleet_size=1,
            base_cost_per_mile=1.0,
            fixed_load_cost=0.0,
            value_scale_dollars=1000.0,
            terminal_value_weight=1.0,
        )
        lanes = [
            {
                "origin_state": "AA",
                "destination_state": "BB",
                "faf_tons_2024": "1.0",
                "faf_tmiles_2024": "0.1",  # 100-mile lane
                "rate_midpoint": "500",
                "scarcity_multiplier": "1.0",
            }
        ]
        # Bypass the calibration stream: zero extra cost and overhead.
        dlp._MEAN_EXTRA_COST[scenario.name] = 0.0
        dlp._MEAN_SCHEDULE_OVERHEAD[scenario.name] = 0.0
        return dlp, scenario, lanes

    def test_terminal_value_earned_exactly_once(self):
        import freight_feasibility as ffeas

        dlp, scenario, lanes = self._setup(horizon_hours=12)
        fleet = {"AA": [ffeas.TruckState("t0", "AA", 0.0)]}
        hi, _ = dlp.solve_potentials(
            scenario, lanes, fleet, 0.0, {"AA": 100.0, "BB": 100.0}
        )
        lo, _ = dlp.solve_potentials(
            scenario, lanes, fleet, 0.0, {"AA": 0.0, "BB": 0.0}
        )
        # One truck, equal terminal values everywhere: raising the
        # terminal by 100 must raise the LP by exactly omega * 100,
        # whether or not the truck dispatches (the double-counting bug
        # made a final-stage dispatch earn it twice).
        self.assertAlmostEqual(hi - lo, 100.0, delta=1e-6)

    def test_post_horizon_truck_adds_no_capacity(self):
        import freight_feasibility as ffeas

        dlp, scenario, lanes = self._setup(horizon_hours=24)
        sv = {"AA": 100.0, "BB": 100.0}
        late = {"AA": [ffeas.TruckState("t0", "AA", 500.0)]}
        with_late, _ = dlp.solve_potentials(scenario, lanes, late, 0.0, sv)
        empty, _ = dlp.solve_potentials(scenario, lanes, {"AA": []}, 0.0, sv)
        # A truck that only becomes available after the horizon must
        # not enter the LP as dispatchable capacity.
        self.assertAlmostEqual(with_late, empty, delta=1e-9)

    def test_stage_count_exact_ceiling(self):
        from scripts import run_dlp_resolve as dlp

        self.assertEqual(dlp.stage_count(24.49), 3)
        self.assertEqual(dlp.stage_count(24.0), 2)
        self.assertEqual(dlp.stage_count(0.5), 1)
        self.assertEqual(dlp.stage_count(12.01), 2)

    def test_resolve_cache_reset_per_simulation(self):
        import run_closed_loop_baselines as rbase
        import run_dlp_resolve as dlp  # bare import: same module object
        import run_surrogate_cascade as rsc  # as simulate_policy uses

        config_scenario = rbase.Scenario(
            name="dlp_cache_micro",
            horizon_hours=2,
            loads_per_hour=1,
            fleet_size=1,
            base_cost_per_mile=1.0,
            fixed_load_cost=0.0,
            value_scale_dollars=1000.0,
            terminal_value_weight=1.0,
        )
        lanes = rbase.load_csv(rbase.LANES)
        sv = rbase.build_state_values(lanes, config_scenario)
        loads = rsc.generate_loads_with_seed(lanes, config_scenario, 1)[:1]
        fleet = rsc.initial_fleet_with_seed(lanes, config_scenario, 1)
        dlp._MEAN_EXTRA_COST[config_scenario.name] = 0.0
        dlp._MEAN_SCHEDULE_OVERHEAD[config_scenario.name] = 0.0
        # A stale entry from a previous stream (id() reuse hazard) must
        # be cleared when a new simulation starts.
        dlp._RESOLVE_STATE[("stale", 0)] = (0.0, {})
        rsc.simulate_policy(
            "dlp_resolve", loads, fleet, lanes, config_scenario, sv, None
        )
        self.assertNotIn(("stale", 0), dlp._RESOLVE_STATE)

    def test_fractional_resolve_time_stage_count(self):
        import freight_feasibility as ffeas

        dlp, scenario, lanes = self._setup(horizon_hours=72)
        fleet = {"AA": [ffeas.TruckState("t0", "AA", 47.51)]}
        # Remaining horizon 72 - 47.51 = 24.49 h must span three
        # 12-hour stages (the integer-division form returned two).
        _, w = dlp.solve_potentials(
            scenario, lanes, fleet, 47.51, {"AA": 0.0, "BB": 0.0}
        )
        self.assertEqual(max(s for _, s in w), 2)

    def test_score_uses_actual_completion(self):
        dlp, scenario, lanes = self._setup(horizon_hours=48)
        fleet = {"AA": []}
        # Pre-seed the resolve cache with synthetic potentials so the
        # score is a pure table lookup.
        w = {("BB", 0): 0.0, ("BB", 1): -500.0, ("AA", 0): 0.0}
        dlp._RESOLVE_STATE[(scenario.name, id(fleet))] = (0.0, w)
        load = {
            "hour": 0.0,
            "origin_state": "AA",
            "destination_state": "BB",
            "travel_hours": 2.0,
        }
        sv = {"AA": 0.0, "BB": 0.0}
        fast = dlp.dlp_score(scenario, lanes, fleet, load, 0.0, sv, done=2.0)
        slow = dlp.dlp_score(scenario, lanes, fleet, load, 0.0, sv, done=14.0)
        # An actual completion in the next stage must read that
        # stage's potential, not the nominal travel-hours stage.
        self.assertAlmostEqual(fast, 0.0, delta=1e-9)
        self.assertAlmostEqual(slow, -500.0, delta=1e-9)


class DlpSimplexTests(unittest.TestCase):
    def test_two_phase_with_equality_row(self):
        from scripts import run_dlp_resolve as dlp

        # max 3x + 2y s.t. x + y = 4, x <= 3, y <= 3  ->  x=3, y=1.
        value, duals = dlp.float_simplex_max(
            [3.0, 2.0],
            [[1.0, 1.0], [1.0, 0.0], [0.0, 1.0]],
            [4.0, 3.0, 3.0],
            ["=", "<=", "<="],
        )
        self.assertAlmostEqual(value, 11.0, places=7)
        # Equality dual = marginal value of the balance rhs (2.0: one
        # more unit goes to y); x-cap dual = 1.0 (3 - 2).
        self.assertAlmostEqual(duals[0], 2.0, places=7)
        self.assertAlmostEqual(duals[1], 1.0, places=7)

    def test_pure_inequality_problem(self):
        from scripts import run_dlp_resolve as dlp

        value, duals = dlp.float_simplex_max(
            [1.0, 1.0],
            [[2.0, 1.0], [1.0, 3.0]],
            [4.0, 6.0],
            ["<=", "<="],
        )
        self.assertAlmostEqual(value, 2.8, places=7)  # x=6/5, y=8/5
        self.assertTrue(all(d >= -1e-9 for d in duals))


class _StubScenario:
    name = "stub"
    horizon_hours = 6


class DualPriceFitTests(unittest.TestCase):
    def test_shrinkage_toward_origin_mean(self):
        loads = [
            {"load_id": 0, "origin_state": "GA", "hour": 1.0},
            {"load_id": 1, "origin_state": "GA", "hour": 1.5},
            {"load_id": 2, "origin_state": "GA", "hour": 9.0},
        ]
        duals = {0: 10.0, 1: 20.0, 2: 40.0}
        rows = fit_dual_prices.fit_table(_StubScenario(), loads, duals)
        by_key = {
            (r["origin_state"], r["hour_bucket"]): float(r["lambda_mean"])
            for r in rows
        }
        origin_mean = (10.0 + 20.0 + 40.0) / 3
        k = fit_dual_prices.SHRINKAGE_PSEUDO_COUNT
        expected_h1 = (10.0 + 20.0 + k * origin_mean) / (2 + k)
        self.assertAlmostEqual(by_key[("GA", 1)], expected_h1, places=3)
        self.assertAlmostEqual(
            by_key[("GA", fit_dual_prices.ALL_HOURS)], origin_mean, places=3
        )


class LaneGranularityTests(unittest.TestCase):
    LOADS = [
        {"load_id": 0, "origin_state": "GA", "destination_state": "TX", "hour": 1.0},
        {"load_id": 1, "origin_state": "GA", "destination_state": "TX", "hour": 1.4},
        {"load_id": 2, "origin_state": "GA", "destination_state": "FL", "hour": 1.6},
        {"load_id": 3, "origin_state": "GA", "destination_state": "FL", "hour": 1.8},
    ]
    DUALS = {0: 100.0, 1: 100.0, 2: 10.0, 3: 10.0}

    def test_lane_table_separates_destinations(self):
        rows = fit_dual_prices.fit_table(
            _StubScenario(), self.LOADS, self.DUALS, granularity="lane"
        )
        by_key = {
            (r["origin_state"], r["dest_state"], r["hour_bucket"]): float(
                r["lambda_mean"]
            )
            for r in rows
        }
        # Within-lane shrinkage targets the lane mean, so the two lanes
        # keep their distinct rents instead of pooling to 55.
        self.assertAlmostEqual(by_key[("GA", "TX", 1)], 100.0, places=4)
        self.assertAlmostEqual(by_key[("GA", "FL", 1)], 10.0, places=4)
        # Market-level fallback rows still pool across the origin.
        self.assertAlmostEqual(by_key[("GA", "*", -1)], 55.0, places=4)

    def test_market_table_pools_destinations(self):
        rows = fit_dual_prices.fit_table(
            _StubScenario(), self.LOADS, self.DUALS, granularity="market"
        )
        by_key = {
            (r["origin_state"], r["dest_state"], r["hour_bucket"]): float(
                r["lambda_mean"]
            )
            for r in rows
        }
        self.assertAlmostEqual(by_key[("GA", "*", 1)], 55.0, places=4)
        self.assertNotIn(("GA", "TX", 1), by_key)

    def test_policy_lookup_prefers_lane_and_falls_back(self):
        from scripts import run_surrogate_cascade as sc

        with mock.patch.object(
            sc,
            "_DUAL_PRICE_TABLE",
            {
                ("s", "GA", "TX", 1): 100.0,
                ("s", "GA", "*", 1): 55.0,
                ("s", "GA", "*", -1): 50.0,
                ("s", "*", "*", -1): 40.0,
            },
        ):
            self.assertEqual(sc.dual_price_lambda("s", "GA", 1.2, dest="TX"), 100.0)
            self.assertEqual(sc.dual_price_lambda("s", "GA", 1.2, dest="FL"), 55.0)
            self.assertEqual(sc.dual_price_lambda("s", "GA", 9.0, dest="FL"), 50.0)
            self.assertEqual(sc.dual_price_lambda("s", "NM", 9.0), 40.0)

    def test_accept_margin_defaults_to_zero(self):
        from scripts import run_surrogate_cascade as sc

        self.assertEqual(sc.ACCEPT_MARGIN, 0.0)


class ValueTogoTests(unittest.TestCase):
    def _fit(self, loads, duals, values):
        with mock.patch.object(
            fit_value_togo.base, "terminal_value_weight", return_value=0.25
        ):
            return fit_value_togo.fit_value_togo(
                _StubScenario(), loads, duals, values
            )

    def test_terminal_row_is_omega_times_state_value(self):
        w = self._fit([], {}, {"GA": 100.0, "TX": 40.0})
        self.assertAlmostEqual(w[("GA", 6)], 25.0)
        self.assertAlmostEqual(w[("TX", 6)], 10.0)

    def test_recursion_is_monotone_and_prices_dispatch(self):
        loads = [
            {
                "load_id": 0,
                "origin_state": "GA",
                "destination_state": "TX",
                "hour": 2.0,
                "price": 100.0,
                "direct_cost": 40.0,
                "travel_hours": 2.0,
            }
        ]
        duals = {0: 15.0}
        w = self._fit(loads, duals, {"GA": 0.0, "TX": 40.0})
        # Wait branch keeps W monotone non-increasing in time.
        for hour in range(6):
            self.assertGreaterEqual(w[("GA", hour)], w[("GA", hour + 1)])
        # At hour 2 the netted dispatch (60 - 15 + W(TX, 4)) beats waiting.
        self.assertAlmostEqual(w[("GA", 2)], 60.0 - 15.0 + w[("TX", 4)])


class AnalysisRegenerationTests(unittest.TestCase):
    def test_paper_headline_numbers_regenerate_from_artifacts(self):
        from scripts import analyze_v04_results as an

        args = type(
            "Args",
            (),
            {
                "seed30_dir": str(REPO / "benchmark_runs/v04_dev/seed30"),
                "mild_dir": str(
                    REPO / "benchmark_runs/v04_dev/seed30_mild_fitted"
                ),
            },
        )()
        rows = an.load_scenario_rows(args)
        methods = {
            m["scenario"]: m
            for m in an.analyze_methods(rows, resamples=4000, seed=20260701)
        }
        self.assertAlmostEqual(
            methods["tight"]["delta_pp_mean"], 2.0, delta=0.1
        )
        self.assertAlmostEqual(
            methods["mild"]["delta_pp_mean"], 3.5, delta=0.1
        )
        # The paper's reported p-values, not just significance flags.
        self.assertAlmostEqual(
            methods["tight"]["wilcoxon_p"], 0.019, delta=0.002
        )
        self.assertAlmostEqual(
            methods["scarce"]["wilcoxon_p"], 0.329, delta=0.005
        )
        self.assertLess(methods["mild"]["wilcoxon_p"], 0.001)
        self.assertEqual(methods["tight"]["sign_wins"], 19)
        self.assertEqual(methods["mild"]["sign_wins"], 26)

        certs = {
            c["scenario"]: c
            for c in an.analyze_certs(
                rows, REPO / "benchmark_runs/v041_fix/certs"
            )
        }
        self.assertAlmostEqual(
            certs["tight"]["dual_price_vf_mean_pct"], 60.1, delta=0.1
        )
        self.assertAlmostEqual(
            certs["scarce"]["dual_price_vf_mean_pct"], 57.6, delta=0.1
        )


if __name__ == "__main__":
    unittest.main()
