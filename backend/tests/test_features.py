"""Tests for SMART feature engineering."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.etl.features import FEATURE_NAMES, extract_features, features_to_vector


class _Row:
    def __init__(self, d, poh, temp, realloc, wear, pct):
        self.date = d
        self.power_on_hours = poh
        self.temperature = temp
        self.reallocated_sectors = realloc
        self.media_wearout_indicator = wear
        self.pct_used = pct


def _rows(n: int) -> list[_Row]:
    base = date(2026, 1, 1)
    return [
        _Row(base + timedelta(days=i), 1000 + i * 24, 30.0 + i, i, i * 0.5, i * 0.4)
        for i in range(n)
    ]


def test_extract_features_values() -> None:
    features = extract_features(_rows(10))
    assert set(features) == set(FEATURE_NAMES)
    assert features["days_observed"] == 10
    assert features["reallocated_delta"] == 9
    assert features["reallocated_sectors"] == 9
    assert features["temp_max"] == 39.0
    assert features["temp_last"] == 39.0
    assert features["power_on_hours"] == 1000 + 9 * 24


def test_features_unsorted_input() -> None:
    rows = _rows(5)
    features = extract_features(list(reversed(rows)))
    assert features["temp_last"] == 34.0  # last chronologically, not last in list


def test_features_to_vector_order() -> None:
    vec = features_to_vector(extract_features(_rows(3)))
    assert len(vec) == len(FEATURE_NAMES)


def test_extract_features_empty_raises() -> None:
    with pytest.raises(ValueError):
        extract_features([])
