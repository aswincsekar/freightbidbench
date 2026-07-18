PYTHON ?= python3
SMOKE_DIR ?= benchmark_runs/ci_smoke
QUICKSTART_DIR ?= benchmark_runs/quickstart
STANDARD_DIR ?= benchmark_runs/standard_v02
PAPER_DIR ?= benchmark_runs/paper_v02
PAPER_V03_DIR ?= benchmark_runs/paper_v03
HINDSIGHT_DIR ?= benchmark_runs/hindsight_bound_smoke
RELAXED_BOUND_DIR ?= benchmark_runs/relaxed_bound_smoke
LAGRANGIAN_BOUND_DIR ?= benchmark_runs/lagrangian_bound_smoke
V03_SWEEP_DIR ?= benchmark_runs/v03_sweeps/service_failure_penalty
V03_TERMINAL_SWEEP_DIR ?= benchmark_runs/v03_sweeps/terminal_value
V03_WAVE_SWEEP_DIR ?= benchmark_runs/v03_sweeps/demand_waves

.PHONY: help compile test smoke quickstart standard figures deltas hindsight-smoke relaxed-bound-smoke lagrangian-bound-smoke v03-penalty-sweep-smoke v03-terminal-sweep-smoke v03-wave-sweep-smoke paper-v03-tables paper-v03-check paper-v03-pdf paper-pdf

help:
	@printf "FreightBidBench local targets:\n"
	@printf "  make test       Compile scripts and run unit tests\n"
	@printf "  make smoke      Run the tiny benchmark contract used by CI\n"
	@printf "  make quickstart Run smoke preset and generate figures\n"
	@printf "  make standard   Run the standard preset into benchmark_runs/standard_v02\n"
	@printf "  make deltas     Compute paired policy deltas for benchmark_runs/paper_v02\n"
	@printf "  make hindsight-smoke Run the v0.3 exact hindsight-bound prototype\n"
	@printf "  make relaxed-bound-smoke Run the v0.3 relaxed full-horizon bound prototype\n"
	@printf "  make lagrangian-bound-smoke Run the v0.3 Lagrangian-per-truck bound (Theorem 1 prototype)\n"
	@printf "  make v03-penalty-sweep-smoke Run a small service-failure penalty sweep\n"
	@printf "  make v03-terminal-sweep-smoke Run a small terminal-value sweep\n"
	@printf "  make v03-wave-sweep-smoke Run a small demand-wave sweep\n"
	@printf "  make paper-v03-tables Assemble v0.3 paper table drafts from existing artifacts\n"
	@printf "  make paper-v03-check  Check v0.3 paper draft and table artifacts exist\n"
	@printf "  make paper-v03-pdf    Build the LaTeX v0.3 paper draft\n"
	@printf "  make paper-pdf  Build the LaTeX paper draft\n"

compile:
	$(PYTHON) -m py_compile scripts/*.py tests/*.py

test: compile
	$(PYTHON) -m unittest discover -s tests

smoke:
	$(PYTHON) scripts/run_freightbidbench.py \
	  --preset smoke \
	  --seed-count 1 \
	  --label-limit 5 \
	  --eval-load-limit 10 \
	  --cascade-bands 0 \
	  --output-dir $(SMOKE_DIR)

quickstart:
	$(PYTHON) scripts/run_freightbidbench.py \
	  --preset smoke \
	  --output-dir $(QUICKSTART_DIR)
	$(PYTHON) scripts/plot_freightbidbench.py \
	  --run-dir $(QUICKSTART_DIR)

standard:
	$(PYTHON) scripts/run_freightbidbench.py \
	  --preset standard \
	  --output-dir $(STANDARD_DIR)
	$(PYTHON) scripts/plot_freightbidbench.py \
	  --run-dir $(STANDARD_DIR)

figures:
	$(PYTHON) scripts/plot_freightbidbench.py \
	  --run-dir $(STANDARD_DIR)

deltas:
	$(PYTHON) scripts/analyze_policy_deltas.py \
	  --run-dir $(PAPER_DIR)

calibration-report:
	$(PYTHON) scripts/analyze_calibration.py

hindsight-smoke:
	$(PYTHON) scripts/run_hindsight_bound.py \
	  --config configs/freightbidbench_v03_scenarios.json \
	  --scenario tight \
	  --max-loads 12 \
	  --output-dir $(HINDSIGHT_DIR)

relaxed-bound-smoke:
	$(PYTHON) scripts/run_relaxed_hindsight_bound.py \
	  --config configs/freightbidbench_v03_scenarios.json \
	  --scenario tight \
	  --eval-load-limit 250 \
	  --skip-policy-comparison \
	  --output-dir $(RELAXED_BOUND_DIR)

lagrangian-bound-smoke:
	$(PYTHON) scripts/run_lagrangian_bound.py \
	  --config configs/freightbidbench_v03_scenarios.json \
	  --scenario tight \
	  --eval-load-limit 200 \
	  --fleet-limit 30 \
	  --iterations 10 \
	  --step-scale 50 \
	  --output-dir $(LAGRANGIAN_BOUND_DIR)

v03-penalty-sweep-smoke:
	$(PYTHON) scripts/run_service_failure_penalty_sweep.py \
	  --preset smoke \
	  --scenarios tight,scarce \
	  --penalties 0,250 \
	  --seed-count 1 \
	  --label-limit 5 \
	  --eval-load-limit 10 \
	  --output-dir $(V03_SWEEP_DIR)

v03-terminal-sweep-smoke:
	$(PYTHON) scripts/run_terminal_value_sweep.py \
	  --preset smoke \
	  --scenarios tight,scarce \
	  --weights 0,0.5 \
	  --seed-count 1 \
	  --label-limit 5 \
	  --eval-load-limit 10 \
	  --output-dir $(V03_TERMINAL_SWEEP_DIR)

v03-wave-sweep-smoke:
	$(PYTHON) scripts/run_demand_wave_sweep.py \
	  --preset smoke \
	  --scenarios tight,scarce \
	  --mode price \
	  --amplitudes 0,0.5 \
	  --seed-count 1 \
	  --label-limit 5 \
	  --eval-load-limit 10 \
	  --output-dir $(V03_WAVE_SWEEP_DIR)

paper-v03-tables:
	$(PYTHON) scripts/assemble_v03_paper_tables.py \
	  --methods-dir benchmark_runs/v03_sweeps/methods_cascade_seed10_label200 \
	  --relaxed-dir benchmark_runs/v03_sweeps/relaxed_bound_tight_full_rollout \
	  --relaxed-dir benchmark_runs/v03_sweeps/relaxed_bound_scarce_full_rollout \
	  --exact-dir benchmark_runs/hindsight_bound_smoke \
	  --output-dir $(PAPER_V03_DIR)

paper-v03-check: paper-v03-tables
	test -s papers/freightbidbench_v03_benchmark_paper.md
	test -s papers/freightbidbench_v03_benchmark_paper.tex
	test -s papers/freightbidbench_v03_runbook.md
	test -s $(PAPER_V03_DIR)/v03_paper_tables.md
	test -s $(PAPER_V03_DIR)/v03_methods_table.csv
	test -s $(PAPER_V03_DIR)/v03_relaxed_bound_table.csv
	test -s $(PAPER_V03_DIR)/v03_exact_hindsight_table.csv

paper-v03-pdf: paper-v03-check
	cd papers && mkdir -p build
	cd papers && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build freightbidbench_v03_benchmark_paper.tex
	cd papers && bibtex build/freightbidbench_v03_benchmark_paper
	cd papers && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build freightbidbench_v03_benchmark_paper.tex
	cd papers && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build freightbidbench_v03_benchmark_paper.tex

paper-trb-pdf:
	cd papers && mkdir -p build
	cd papers && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build freightbidbench_trb2027.tex
	cd papers && bibtex build/freightbidbench_trb2027
	cd papers && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build freightbidbench_trb2027.tex
	cd papers && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build freightbidbench_trb2027.tex

paper-pdf:
	cd papers && mkdir -p build
	cd papers && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build freightbidbench_v02_benchmark_paper.tex
	cd papers && bibtex build/freightbidbench_v02_benchmark_paper
	cd papers && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build freightbidbench_v02_benchmark_paper.tex
	cd papers && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build freightbidbench_v02_benchmark_paper.tex

paper-v04-pdf:
	cd papers && mkdir -p build
	cd papers && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build freightbidbench_v04_methods_paper.tex
	cd papers && bibtex build/freightbidbench_v04_methods_paper
	cd papers && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build freightbidbench_v04_methods_paper.tex
	cd papers && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build freightbidbench_v04_methods_paper.tex
