"""Tests for the /drives endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_drives(seeded, client: TestClient) -> None:
    resp = client.get("/drives")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 12
    assert len(body["items"]) == 12
    # No predictions have been made yet in Phase 2.
    assert body["items"][0]["latest_failure_probability"] is None


def test_list_drives_status_filter(seeded, client: TestClient) -> None:
    resp = client.get("/drives", params={"status": "failed"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    assert all(item["status"] == "failed" for item in items)


def test_list_drives_pagination(seeded, client: TestClient) -> None:
    resp = client.get("/drives", params={"limit": 5, "offset": 0})
    body = resp.json()
    assert len(body["items"]) == 5
    assert body["total"] == 12
    assert body["limit"] == 5


def test_drive_detail(seeded, client: TestClient) -> None:
    drive_id = client.get("/drives").json()["items"][0]["id"]
    resp = client.get(f"/drives/{drive_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == drive_id
    assert len(body["telemetry"]) > 0
    dates = [pt["date"] for pt in body["telemetry"]]
    assert dates == sorted(dates)  # chronological
    assert body["latest_prediction"] is None


def test_drive_detail_not_found(client: TestClient) -> None:
    resp = client.get("/drives/999999")
    assert resp.status_code == 404
