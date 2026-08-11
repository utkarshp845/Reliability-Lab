COMPOSE ?= docker compose
COMPOSE_OTEL ?= $(COMPOSE) -f docker-compose.yml -f infra/docker/docker-compose.otel.yml
COMPOSE_DASHBOARD ?= $(COMPOSE) -f docker-compose.yml -f infra/docker/docker-compose.dashboard.yml
PYTHON ?= python

.PHONY: up down logs build test lint generate-traffic analyze-logs evaluate-assistant validate format otel-up otel-down otel-logs dashboard-up dashboard-down dashboard-logs

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f demo-service ai-sre-assistant

# Optional: run the same stack with a local OpenTelemetry Collector attached.
# See docs/23-otel-collector-path.md.
otel-up:
	$(COMPOSE_OTEL) up --build -d

otel-down:
	$(COMPOSE_OTEL) down

otel-logs:
	$(COMPOSE_OTEL) logs -f otel-collector

# Optional: run the same stack with Prometheus + Grafana attached, scraping
# each service's existing /metrics endpoint. See docs/24-dashboard-and-alert.md.
dashboard-up:
	$(COMPOSE_DASHBOARD) up --build -d

dashboard-down:
	$(COMPOSE_DASHBOARD) down

dashboard-logs:
	$(COMPOSE_DASHBOARD) logs -f prometheus grafana

build:
	$(COMPOSE) build demo-service ai-sre-assistant

test: build
	$(COMPOSE) run --rm --no-deps demo-service pytest -q
	$(COMPOSE) run --rm --no-deps ai-sre-assistant pytest -q

lint: build
	$(COMPOSE) run --rm --no-deps demo-service ruff check app tests
	$(COMPOSE) run --rm --no-deps ai-sre-assistant ruff check app cli tests

generate-traffic:
	$(PYTHON) scripts/generate-demo-traffic.py --base-url http://localhost:8000

analyze-logs:
	$(COMPOSE) run --rm --no-deps ai-sre-assistant python cli/sre.py analyze --max-lines 120

evaluate-assistant: build
	$(COMPOSE) run --rm --no-deps ai-sre-assistant python -m evals.run_evals

validate: test lint evaluate-assistant
	@echo "Production-readiness validation passed."

format:
	$(COMPOSE) run --rm --no-deps demo-service ruff format app tests
	$(COMPOSE) run --rm --no-deps ai-sre-assistant ruff format app cli tests

