# AI Virtual Hospital (AI-VH) Makefile
# Standard development, testing, and lifecycle targets

PYTHON ?= python3
PYTEST ?= pytest

.PHONY: all help lint typecheck test-unit test-integration test-regression eval test-all up down clean

help:
	@echo "AI-VH Build & Test Targets:"
	@echo "  lint             - Run secret scanner and ruff"
	@echo "  typecheck        - Run mypy type checker on src/vh"
	@echo "  test-unit        - Run fast unit tests"
	@echo "  test-integration - Run integration tests"
	@echo "  test-regression  - Run regression test suite"
	@echo "  eval             - Run evaluation and safety tests"
	@echo "  test-all         - Run lint, typecheck, and full test suite"
	@echo "  up               - Spin up PostgreSQL services via docker compose"
	@echo "  down             - Tear down docker compose services"

lint:
	$(PYTHON) scripts/scan_secrets.py
	ruff check .

typecheck:
	mypy src/vh

test-unit:
	$(PYTEST) -m unit

test-integration:
	$(PYTEST) -m integration

test-regression:
	$(PYTEST) -m regression

GOLDEN ?= v1
PIPELINE ?= dummy

eval:
	$(PYTHON) -m eval.harness.runner --golden $(GOLDEN) --pipeline $(PIPELINE)

test-all: lint typecheck
	$(PYTEST)

up:
	docker compose up -d

down:
	docker compose down

clean:
	rm -rf .pytest_cache .ruff_cache __pycache__ */__pycache__ */*/__pycache__
