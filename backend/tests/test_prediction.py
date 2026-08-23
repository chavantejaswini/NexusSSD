"""Tests for training, the prediction service, and the /predict endpoint."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import settings
from app.etl.features import FEATURE_NAMES
from app.etl.loader import load_source
from app.etl.sources.synthetic import SyntheticSource
from app.ml import storage
from app.ml.train import train
from app.models.fleet import Alert, Prediction
from app.services import prediction_service


@pytest.fixture()
def trained(tmp_path, db_session, monkeypatch):
    """Seed a sizable fleet, train a model into a temp artifact dir, return metadata."""
    source = SyntheticSource(
        num_drives=120, days=120, seed=13, failure_rate=0.35, end_date=date(2026, 1, 31)
    )
    load_source(source, db_session)
    monkeypatch.setattr(settings, "model_artifact_dir", str(tmp_path))
    prediction_service.reload_model()
    metadata = train(horizon_days=30, seed=42)
    prediction_service.reload_model()
    return metadata


def test_training_produces_artifacts_and_signal(trained) -> None:
    assert storage.model_exists()
    assert trained["n_positive"] >= 5
    assert trained["n_negative"] >= 5
    assert trained["feature_names"] == FEATURE_NAMES
    # The injected pre-failure signal is strong; the model should separate well.
    assert trained["metrics"]["roc_auc"] >= 0.8
    assert 0.0 <= trained["threshold"] <= 1.0


def test_predict_for_drive_endpoint(trained, client: TestClient) -> None:
    drive_id = client.get("/drives", params={"limit": 1}).json()["items"][0]["id"]
    resp = client.post("/predict", json={"drive_id": drive_id})
    assert resp.status_code == 200
    body = resp.json()
    assert body["drive_id"] == drive_id
    assert 0.0 <= body["failure_probability"] <= 1.0
    assert body["band"] in {"low", "medium", "high"}
    assert len(body["top_features"]) == 5
    assert body["model_version"] == trained["model_version"]


def test_predict_from_features_endpoint(trained, client: TestClient) -> None:
    features = {name: 1.0 for name in FEATURE_NAMES}
    resp = client.post("/predict", json={"features": features})
    assert resp.status_code == 200
    assert resp.json()["drive_id"] is None


def test_predict_requires_exactly_one_input(client: TestClient) -> None:
    assert client.post("/predict", json={}).status_code == 422
    both = {"drive_id": 1, "features": {name: 0.0 for name in FEATURE_NAMES}}
    assert client.post("/predict", json=both).status_code == 422


def test_predict_missing_features_is_422(trained, client: TestClient) -> None:
    resp = client.post("/predict", json={"features": {"power_on_hours": 1.0}})
    assert resp.status_code == 422


def test_predict_untrained_returns_503(client: TestClient, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "model_artifact_dir", str(tmp_path))  # empty dir
    prediction_service.reload_model()
    features = {name: 0.0 for name in FEATURE_NAMES}
    resp = client.post("/predict", json={"features": features})
    assert resp.status_code == 503


def test_score_fleet_populates_predictions(trained, db_session) -> None:
    stats = prediction_service.score_fleet(db_session)
    assert stats.scored > 0

    n_pred = db_session.execute(select(func.count()).select_from(Prediction)).scalar_one()
    assert n_pred == stats.scored

    # A high-failure fleet should trip at least one alert.
    n_alerts = db_session.execute(select(func.count()).select_from(Alert)).scalar_one()
    assert n_alerts == stats.alerts_created
    assert stats.alerts_created >= 1
