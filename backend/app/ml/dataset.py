"""Build a labeled training dataset from stored telemetry.

For each drive we slide an "as-of" date across its history. At each as-of date we
compute features from a trailing window and label the example 1 if the drive
fails within `horizon_days` after that date, else 0. This teaches the model to
recognize the pre-failure signal (rising temperature / reallocated sectors /
wear) rather than just the failure itself.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.etl.features import extract_features, features_to_vector
from app.models.drive import Drive, DriveStatus
from app.models.telemetry import Telemetry

WINDOW_DAYS = 14  # trailing telemetry window used to compute features
STEP_DAYS = 3  # spacing between as-of snapshots
MIN_WINDOW_ROWS = 3


@dataclass
class Dataset:
    X: np.ndarray
    y: np.ndarray

    @property
    def num_positive(self) -> int:
        return int(self.y.sum())

    @property
    def num_negative(self) -> int:
        return int(len(self.y) - self.y.sum())


def build_dataset(session: Session, horizon_days: int) -> Dataset:
    features: list[list[float]] = []
    labels: list[int] = []

    drives = session.execute(select(Drive)).scalars().all()
    for drive in drives:
        rows = list(
            session.execute(
                select(Telemetry)
                .where(Telemetry.drive_id == drive.id)
                .order_by(Telemetry.date)
            ).scalars()
        )
        if len(rows) < MIN_WINDOW_ROWS:
            continue

        failure_date = (
            drive.last_seen if drive.status == DriveStatus.FAILED.value else None
        )

        for i in range(len(rows) - 1, -1, -STEP_DAYS):
            as_of = rows[i].date
            window = [
                r for r in rows if r.date <= as_of and (as_of - r.date).days < WINDOW_DAYS
            ]
            if len(window) < MIN_WINDOW_ROWS:
                continue

            if failure_date is not None:
                days_to_fail = (failure_date - as_of).days
                label = 1 if 0 <= days_to_fail <= horizon_days else 0
            else:
                label = 0

            features.append(features_to_vector(extract_features(window)))
            labels.append(label)

    return Dataset(X=np.array(features, dtype=float), y=np.array(labels, dtype=int))
