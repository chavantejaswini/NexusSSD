"""Tests for the observability layer: /metrics and request middleware."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from app.etl.loader import load_source
from app.etl.sources.synthetic import SyntheticSource


def test_metrics_endpoint_exposes_prometheus(client: TestClient) -> None:
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    body = resp.text
    assert "http_requests_total" in body
    assert "nexus_drives_total" in body
    assert "http_request_duration_seconds" in body


def test_metrics_reflect_fleet(client: TestClient, db_session) -> None:
    load_source(
        SyntheticSource(num_drives=8, days=20, seed=1, end_date=date(2026, 1, 20)),
        db_session,
    )
    body = client.get("/metrics").text
    # gauge line like: nexus_drives_total 8.0
    line = next(
        ln for ln in body.splitlines() if ln.startswith("nexus_drives_total ")
    )
    assert float(line.split()[1]) == 8.0


def test_request_id_header_present(client: TestClient) -> None:
    resp = client.get("/health")
    assert "x-request-id" in {k.lower() for k in resp.headers}


def test_incoming_request_id_is_echoed(client: TestClient) -> None:
    resp = client.get("/health", headers={"X-Request-ID": "test-corr-123"})
    assert resp.headers["x-request-id"] == "test-corr-123"
