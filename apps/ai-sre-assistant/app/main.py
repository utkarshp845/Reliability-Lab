from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel, Field

from app.analyzer import analyze_logs
from app.llm import analyze_with_llm, cost_controls_summary, estimate_cost, load_config
from app.log_reader import get_log_path, read_recent_logs
from app.logging_config import logger
from app.metrics_analyzer import analyze_metrics, combined_incident_analysis
from app.metrics_reader import fetch_metrics_text, get_metrics_url, parse_prometheus_text
from app.provider_metrics import PROVIDER_METRICS
from app.redaction import redact_data, redact_text
from app.request_context import current_request_id, reset_request_id, set_request_id


app = FastAPI(
    title="ai-sre-assistant",
    description="An evidence-grounded operational assistant for the demo-service.",
    version="0.1.0",
)


@app.middleware("http")
async def record_requests(request: Request, call_next):
    # Same header and field name demo-service uses, so a shared request_id
    # can be threaded through an operator workflow that touches both services.
    request_id = request.headers.get("x-request-id", str(uuid4()))
    request_id_token = set_request_id(request_id)
    start = perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["x-request-id"] = request_id
        return response
    except Exception:
        logger.exception(
            "unhandled_request_error",
            extra={
                "event": "unhandled_request_error",
                "method": request.method,
                "path": request.url.path,
                "request_id": request_id,
            },
        )
        raise
    finally:
        duration_ms = round((perf_counter() - start) * 1000, 2)
        logger.info(
            "request_completed",
            extra={
                "event": "request_completed",
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "request_id": request_id,
            },
        )
        reset_request_id(request_id_token)


class AnalyzeLogsRequest(BaseModel):
    max_lines: int = Field(default=100, ge=1, le=1000)
    use_llm: bool = True


class AnalyzeMetricsRequest(BaseModel):
    metrics_url: str | None = Field(default=None, max_length=1000)
    metrics_text: str | None = Field(default=None, max_length=100_000)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    max_lines: int = Field(default=100, ge=1, le=1000)
    use_llm: bool = True


class SummarizeIncidentRequest(BaseModel):
    max_lines: int = Field(default=200, ge=1, le=1000)
    metrics_url: str | None = Field(default=None, max_length=1000)
    metrics_text: str | None = Field(default=None, max_length=100_000)
    include_metrics: bool = True
    use_llm: bool = True


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "ai-sre-assistant"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=PROVIDER_METRICS.render_prometheus(), media_type="text/plain")


@app.post("/analyze/logs")
def analyze_recent_logs(request: AnalyzeLogsRequest) -> dict[str, Any]:
    return _analyze(question="What happened recently in demo-service logs?", max_lines=request.max_lines, use_llm=request.use_llm)


@app.post("/analyze/metrics")
def analyze_recent_metrics(request: AnalyzeMetricsRequest) -> dict[str, Any]:
    return _analyze_metrics(metrics_url=request.metrics_url, metrics_text=request.metrics_text)


@app.post("/ask")
def ask(request: AskRequest) -> dict[str, Any]:
    return _analyze(question=request.question, max_lines=request.max_lines, use_llm=request.use_llm)


@app.post("/summarize-incident")
def summarize_incident(request: SummarizeIncidentRequest) -> dict[str, Any]:
    question = "Summarize the last incident using demo-service logs and metrics."
    log_response = _analyze(question=question, max_lines=request.max_lines, use_llm=False)
    metrics_response = (
        _analyze_metrics(metrics_url=request.metrics_url, metrics_text=request.metrics_text)
        if request.include_metrics
        else {"metrics_analysis": analyze_metrics([], source=None)}
    )

    log_analysis = log_response["rule_based_analysis"]
    metrics_analysis = metrics_response["metrics_analysis"]
    combined = combined_incident_analysis(log_analysis=log_analysis, metrics_analysis=metrics_analysis)

    response: dict[str, Any] = {
        "question": question,
        "analysis_mode": "rule-based",
        "log_path": log_response["log_path"],
        "logs_read": log_response["logs_read"],
        "correlated_request_ids": log_response["correlated_request_ids"],
        "metrics_source": metrics_response.get("metrics_source"),
        "metrics_notice": metrics_response.get("metrics_notice"),
        "log_analysis": log_analysis,
        "metrics_analysis": metrics_analysis,
        "combined_analysis": combined,
    }

    if request.use_llm:
        llm_config = load_config()
        response["llm_cost_controls"] = cost_controls_summary(llm_config)
        llm_result = analyze_with_llm(
            question=question,
            logs=[],
            rule_based_analysis=response,
            config=llm_config,
        )
        response["llm_telemetry"] = llm_result.telemetry
        response["llm_cost_estimate"] = estimate_cost(llm_config, llm_result.telemetry)
        if llm_result.analysis:
            response["analysis_mode"] = "llm"
            response["llm_analysis"] = llm_result.analysis
        if llm_result.notice:
            response["llm_notice"] = llm_result.notice

    return redact_data(response)


def _analyze(question: str, max_lines: int, use_llm: bool) -> dict[str, Any]:
    question = redact_text(question)
    log_path = get_log_path()
    logs = read_recent_logs(log_path=log_path, max_lines=max_lines)
    rule_based = analyze_logs(logs, question=question)

    response: dict[str, Any] = {
        "question": question,
        "analysis_mode": "rule-based",
        "log_path": str(log_path),
        "logs_read": len(logs),
        "correlated_request_ids": rule_based["correlated_request_ids"],
        "rule_based_analysis": rule_based,
    }

    if use_llm:
        llm_config = load_config()
        response["llm_cost_controls"] = cost_controls_summary(llm_config)
        llm_result = analyze_with_llm(
            question=question,
            logs=logs,
            rule_based_analysis=rule_based,
            config=llm_config,
        )
        response["llm_telemetry"] = llm_result.telemetry
        response["llm_cost_estimate"] = estimate_cost(llm_config, llm_result.telemetry)
        if llm_result.analysis:
            response["analysis_mode"] = "llm"
            response["llm_analysis"] = llm_result.analysis
        if llm_result.notice:
            response["llm_notice"] = llm_result.notice

    logger.info(
        "analysis_completed",
        extra={
            "event": "analysis_completed",
            "analysis_mode": response["analysis_mode"],
            "logs_read": len(logs),
            "correlated_request_ids": response["correlated_request_ids"],
            "request_id": current_request_id(),
        },
    )

    return redact_data(response)


def _analyze_metrics(metrics_url: str | None, metrics_text: str | None) -> dict[str, Any]:
    source = metrics_url or ("request_body" if metrics_text is not None else get_metrics_url())
    notice = None

    if metrics_text is None:
        metrics_text, notice = fetch_metrics_text(metrics_url=metrics_url)

    samples = parse_prometheus_text(metrics_text or "")
    metrics_analysis = analyze_metrics(samples=samples, source=source)

    response: dict[str, Any] = {
        "analysis_mode": "rule-based",
        "metrics_source": source,
        "metrics_samples_read": len(samples),
        "metrics_analysis": metrics_analysis,
    }
    if notice:
        response["metrics_notice"] = notice

    return redact_data(response)
