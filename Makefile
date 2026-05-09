PYTHON ?= python3
SMOKE_DIR ?= benchmark_runs/ci_smoke
QUICKSTART_DIR ?= benchmark_runs/quickstart
STANDARD_DIR ?= benchmark_runs/standard_v02
PAPER_DIR ?= benchmark_runs/paper_v02

.PHONY: help compile test smoke quickstart standard figures deltas paper-pdf

help:
	@printf "FreightBidBench local targets:\n"
	@printf "  make test       Compile scripts and run unit tests\n"
	@printf "  make smoke      Run the tiny benchmark contract used by CI\n"
	@printf "  make quickstart Run smoke preset and generate figures\n"
	@printf "  make standard   Run the standard preset into benchmark_runs/standard_v02\n"
	@printf "  make deltas     Compute paired policy deltas for benchmark_runs/paper_v02\n"
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

paper-pdf:
	cd papers && mkdir -p build
	cd papers && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build freightbidbench_v02_benchmark_paper.tex
	cd papers && bibtex build/freightbidbench_v02_benchmark_paper
	cd papers && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build freightbidbench_v02_benchmark_paper.tex
	cd papers && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build freightbidbench_v02_benchmark_paper.tex
