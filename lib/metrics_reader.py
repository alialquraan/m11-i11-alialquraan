"""PROVIDED helper for reading the M11-instrumented backend's /metrics endpoint.

Wraps httpx.get("/metrics") + prometheus_client.parser.text_string_to_metric_families.
Exposes three convenience accessors:

    get_request_count(path)
    get_error_rate(path)
    get_p95_latency(path)

Read this module's code so you understand the parser output, but you do not
need to modify it. The Integration eval harnesses import these helpers and
use them in eval_runner.py to populate the report's "Derived /metrics Signals"
section.
"""
from __future__ import annotations

import os
from typing import Optional

import httpx
from prometheus_client.parser import text_string_to_metric_families


API_URL = os.environ.get("API_URL", "http://localhost:8000")


def scrape_metrics(api_url: Optional[str] = None) -> str:
    """Fetch the raw OpenMetrics text body.

    `app.mount("/metrics", make_asgi_app())` serves the metrics at the
    trailing-slash path `/metrics/`; a request to `/metrics` returns a
    307 redirect. httpx does not follow redirects by default, so we pass
    `follow_redirects=True` -- without it, raise_for_status() would raise
    HTTPStatusError on the 307 and abort eval_runner.py at the "Derived
    /metrics Signals" step for every learner.
    """
    url = (api_url or API_URL).rstrip("/") + "/metrics"
    resp = httpx.get(url, timeout=10.0, follow_redirects=True)
    resp.raise_for_status()
    return resp.text


def _families(body: str):
    return list(text_string_to_metric_families(body))


def get_request_count(path: str, body: Optional[str] = None) -> float:
    """Total `requests_total` count for the given path label (any status)."""
    body = body if body is not None else scrape_metrics()
    total = 0.0
    for fam in _families(body):
        if fam.name != "requests":
            continue
        for sample in fam.samples:
            if sample.name == "requests_total" and sample.labels.get("path") == path:
                total += sample.value
    return total


def get_error_rate(path: str, body: Optional[str] = None) -> float:
    """Fraction of `requests_total{path=<path>}` samples whose status is 4xx or 5xx."""
    body = body if body is not None else scrape_metrics()
    total = 0.0
    errors = 0.0
    for fam in _families(body):
        if fam.name != "requests":
            continue
        for sample in fam.samples:
            if sample.name != "requests_total":
                continue
            if sample.labels.get("path") != path:
                continue
            total += sample.value
            status = sample.labels.get("status", "")
            if status and (status.startswith("4") or status.startswith("5")):
                errors += sample.value
    if total == 0:
        return 0.0
    return errors / total


def get_p95_latency(path: str, body: Optional[str] = None) -> float:
    """Estimate p95 latency (seconds) for the given path from the histogram buckets.

    Linear interpolation across the bucket containing the 95th-percentile sample.
    Returns 0.0 if no observations have been recorded for the path.
    """
    body = body if body is not None else scrape_metrics()

    buckets = []  # list of (upper_bound, cumulative_count)
    total_count = 0.0
    for fam in _families(body):
        if fam.name != "request_latency_seconds":
            continue
        for sample in fam.samples:
            if sample.labels.get("path") != path:
                continue
            if sample.name == "request_latency_seconds_bucket":
                le = sample.labels.get("le")
                if le is None:
                    continue
                ub = float("inf") if le == "+Inf" else float(le)
                buckets.append((ub, sample.value))
            elif sample.name == "request_latency_seconds_count":
                total_count = sample.value

    if total_count == 0 or not buckets:
        return 0.0

    buckets.sort(key=lambda x: x[0])
    target = 0.95 * total_count
    prev_ub = 0.0
    prev_count = 0.0
    for ub, cum in buckets:
        if cum >= target:
            if ub == float("inf"):
                return prev_ub
            if cum == prev_count:
                return ub
            fraction = (target - prev_count) / (cum - prev_count)
            return prev_ub + fraction * (ub - prev_ub)
        prev_ub = ub
        prev_count = cum
    return prev_ub



def get_total_requests(path: str, body: Optional[str] = None) -> float:
    """Alias for get_request_count to satisfy eval_runner.py expectations."""
    return get_request_count(path, body=body)