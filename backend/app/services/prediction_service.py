"""Serving-side prediction: load the trained model and score drives.

Computes features identically to training (via app.etl.features) so serving and
training never drift. The loaded model + metadata are cached process-wide;
`reload_model()` clears the cache (used by tests after retraining).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session
from xgboost import XGBClassifier

from app.core.logging import get_logger
from app.etl.features import FEATURE_NAMES, extract_features, features_to_vector
from app.ml import storage
from app.ml.dataset import WINDOW_DAYS
from app.models.drive import Drive
from app.models.fleet import Alert, Prediction
from app.models.telemetry import Telemetry

logger = get_logger(__name__)

# Probability band cutoffs.
_BAND_MEDIUM = 0.30
_BAND_HIGH = 0.70


class ModelNotTrainedError(RuntimeError):
    """No model artifact is available yet."""


class InvalidFeaturesError(ValueError):
    """Provided feature payload is missing required fields."""


class DriveHasNoTelemetryError(RuntimeError):
    """A drive exists but has no telemetry to score."""


_model: XGBClassifier | None = None
_metadata: dict | None = None


def reload_model() -> None:
    global _model, _metadata
    _model = None
    _metadata = None


def _ensure_loaded() -> tuple[XGBClassifier, dict]:
    global _model, _metadata
    if _model is None or _metadata is None:
        if not storage.model_exists():
            raise ModelNotTrainedError(
                "No trained model found. Run `python -m app.ml.train` first."
            )
        model = XGBClassifier()
        model.load_model(str(storage.model_path()))
        _model = model
        _metadata = storage.load_metadata()
    return _model, _metadata


def _band(probability: float) -> str:
    if probability >= _BAND_HIGH:
        return "high"
    if probability >= _BAND_MEDIUM:
        return "medium"
    return "low"


def _top_features(features: dict[str, float], metadata: dict, n: int = 5) -> list[dict]:
    importances: dict[str, float] = metadata.get("feature_importances", {})
    ranked = sorted(FEATURE_NAMES, key=lambda name: importances.get(name, 0.0), reverse=True)
    return [
        {
            "name": name,
            "value": float(features.get(name, 0.0)),
            "importance": float(importances.get(name, 0.0)),
        }
        for name in ranked[:n]
    ]


def predict_from_features(features: dict[str, float]) -> dict:
    model, metadata = _ensure_loaded()
    missing = [name for name in FEATURE_NAMES if name not in features]
    if missing:
        raise InvalidFeaturesError(f"missing features: {missing}")

    vector = features_to_vector(features)
    probability = float(model.predict_proba([vector])[0, 1])
    return {
        "failure_probability": probability,
        "band": _band(probability),
        "model_version": metadata["model_version"],
        "horizon_days": int(metadata["horizon_days"]),
        "top_features": _top_features(features, metadata),
    }


def _recent_window(session: Session, drive_id: int) -> list[Telemetry]:
    rows = list(
        session.execute(
            select(Telemetry)
            .where(Telemetry.drive_id == drive_id)
            .order_by(Telemetry.date.desc())
            .limit(WINDOW_DAYS)
        ).scalars()
    )
    rows.reverse()
    return rows


def predict_for_drive(session: Session, drive_id: int) -> dict | None:
    drive = session.get(Drive, drive_id)
    if drive is None:
        return None
    window = _recent_window(session, drive_id)
    if not window:
        raise DriveHasNoTelemetryError(f"drive {drive_id} has no telemetry")

    features = extract_features(window)
    result = predict_from_features(features)
    result["drive_id"] = drive_id
    return result


@dataclass
class ScoreStats:
    scored: int = 0
    skipped_no_telemetry: int = 0
    alerts_created: int = 0
    metrics: dict = field(default_factory=dict)


def score_fleet(session: Session) -> ScoreStats:
    """Score every drive, persist predictions, and raise alerts for high risk."""
    _, metadata = _ensure_loaded()
    threshold = float(metadata.get("threshold", _BAND_HIGH))
    horizon = int(metadata["horizon_days"])
    version = metadata["model_version"]

    stats = ScoreStats()
    drives = session.execute(select(Drive)).scalars().all()
    for drive in drives:
        window = _recent_window(session, drive.id)
        if not window:
            stats.skipped_no_telemetry += 1
            continue

        features = extract_features(window)
        result = predict_from_features(features)
        probability = result["failure_probability"]

        session.add(
            Prediction(
                drive_id=drive.id,
                model_version=version,
                failure_probability=probability,
                horizon_days=horizon,
                features=features,
            )
        )
        stats.scored += 1

        if probability >= threshold and not _has_open_alert(session, drive.id):
            severity = "critical" if probability >= 0.85 else "warning"
            session.add(
                Alert(
                    drive_id=drive.id,
                    severity=severity,
                    message=(
                        f"Predicted failure probability {probability:.0%} within "
                        f"{horizon} days (model {version})."
                    ),
                )
            )
            stats.alerts_created += 1

    session.commit()
    stats.metrics = {
        "scored": stats.scored,
        "alerts_created": stats.alerts_created,
        "threshold": threshold,
    }
    logger.info("fleet scored", extra=stats.metrics)
    return stats


def _has_open_alert(session: Session, drive_id: int) -> bool:
    return (
        session.execute(
            select(Alert.id).where(
                Alert.drive_id == drive_id, Alert.acknowledged.is_(False)
            )
        ).first()
        is not None
    )
