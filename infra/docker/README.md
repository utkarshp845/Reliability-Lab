# Docker

Docker Compose is the Day 1 runtime for this project.

It starts:

- `demo-service` on port `8000`.
- `ai-sre-assistant` on port `8001`.

Both containers mount `./logs` to `/shared/logs`, which lets the assistant read the demo service log file.

## Commands

```bash
make up
make logs
make down
```

## Optional: OpenTelemetry Collector

`docker-compose.otel.yml` in this directory is an overlay, not a standalone file - it adds a local `otel-collector` service and points both apps at it, without changing what `make up` starts.

```bash
make otel-up
make otel-logs
make otel-down
```

See [`docs/23-otel-collector-path.md`](../../docs/23-otel-collector-path.md) for what it demonstrates and why it stays opt-in.

## Optional: Dashboard And Alert

`docker-compose.dashboard.yml` in this directory is another overlay - it adds Prometheus and Grafana, scraping the `/metrics` endpoints both apps already expose, without changing what `make up` starts.

```bash
make dashboard-up
make dashboard-logs
make dashboard-down
```

Grafana: <http://localhost:3000> (anonymous viewer access - dashboard is provisioned automatically). Prometheus: <http://localhost:9090>.

See [`docs/24-dashboard-and-alert.md`](../../docs/24-dashboard-and-alert.md) for the one dashboard, the one alert, and how to trigger it locally.

## Why Compose First

Compose keeps the first learning loop short:

- Build local images.
- Run multiple services.
- Share a local log volume.
- Avoid Kubernetes until the basic workflow is clear.

