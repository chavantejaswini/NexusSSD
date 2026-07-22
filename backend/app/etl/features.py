"""SMART feature engineering.

Turns a drive's chronological telemetry into a fixed feature vector used by the
prediction model (Phase 3). Kept dependency-light (stdlib only) and shared
between the API prediction service and the offline training pipeline so training
and serving compute identical features.

Accepts any objects exposing the telemetry attributes (ORM `Telemetry` rows or
ETL `TelemetryRecord`s).
"""

from __future__ import annotations

from typing import Protocol

# Canonical ordered feature names. Order matters for the model input vector.
FEATURE_NAMES: list[str] = [
    "power_on_hours",
    "temp_last",
    "temp_mean",
    "temp_max",
    "reallocated_sectors",
    "reallocated_delta",
    "wearout_pct",
    "wearout_delta",
    "pct_used",
    "days_observed",
]


class TelemetryLike(Protocol):
    date: object  # datetime.date
    power_on_hours: int
    temperature: float
    reallocated_sectors: int
    media_wearout_indicator: float
    pct_used: float


def extract_features(rows: list[TelemetryLike]) -> dict[str, float]:
    """Compute the feature dict from a drive's telemetry window.

    Rows may be in any order; they are sorted by date internally.
    Raises ValueError if `rows` is empty.
    """
    if not rows:
        raise ValueError("cannot extract features from empty telemetry")

    ordered = sorted(rows, key=lambda r: r.date)
    first, last = ordered[0], ordered[-1]
    temps = [r.temperature for r in ordered]

    days_observed = (last.date - first.date).days + 1  # type: ignore[operator]

    return {
        "power_on_hours": float(last.power_on_hours),
        "temp_last": float(last.temperature),
        "temp_mean": sum(temps) / len(temps),
        "temp_max": max(temps),
        "reallocated_sectors": float(last.reallocated_sectors),
        "reallocated_delta": float(last.reallocated_sectors - first.reallocated_sectors),
        "wearout_pct": float(last.media_wearout_indicator),
        "wearout_delta": float(
            last.media_wearout_indicator - first.media_wearout_indicator
        ),
        "pct_used": float(last.pct_used),
        "days_observed": float(days_observed),
    }


def features_to_vector(features: dict[str, float]) -> list[float]:
    """Order a feature dict into the canonical model input vector."""
    return [features[name] for name in FEATURE_NAMES]
