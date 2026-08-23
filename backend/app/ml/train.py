"""XGBoost failure-prediction training pipeline.

Builds a labeled dataset from stored telemetry, trains an XGBClassifier,
evaluates it (ROC-AUC, PR-AUC, Brier, calibration curve, confusion matrix),
picks an operating threshold, and saves the model + metadata to ml/artifacts/.

CLI:
    python -m app.ml.train                 # train from the current database
    python -m app.ml.train --score         # also score the fleet afterwards
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from app.core.logging import configure_logging, get_logger
from app.db.session import SessionLocal
from app.etl.features import FEATURE_NAMES
from app.ml import storage
from app.ml.dataset import build_dataset

logger = get_logger(__name__)


class InsufficientDataError(RuntimeError):
    """Raised when the dataset lacks enough positive/negative examples to train."""


def _best_f1_threshold(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Pick the probability threshold maximizing F1 over a coarse grid."""
    best_t, best_f1 = 0.5, -1.0
    for t in np.linspace(0.05, 0.95, 19):
        f1 = f1_score(y_true, (y_prob >= t).astype(int), zero_division=0)
        if f1 > best_f1:
            best_t, best_f1 = float(t), float(f1)
    return best_t


def train(horizon_days: int, seed: int = 42) -> dict:
    session = SessionLocal()
    try:
        dataset = build_dataset(session, horizon_days=horizon_days)
    finally:
        session.close()

    if dataset.num_positive < 5 or dataset.num_negative < 5:
        raise InsufficientDataError(
            f"need >=5 of each class; got {dataset.num_positive} positive / "
            f"{dataset.num_negative} negative. Seed more telemetry first."
        )

    X_train, X_test, y_train, y_test = train_test_split(
        dataset.X, dataset.y, test_size=0.25, random_state=seed, stratify=dataset.y
    )

    pos = max(1, int(y_train.sum()))
    neg = max(1, int(len(y_train) - y_train.sum()))
    model = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        scale_pos_weight=neg / pos,
        eval_metric="logloss",
        random_state=seed,
        n_jobs=2,
    )
    model.fit(X_train, y_train)

    y_prob = model.predict_proba(X_test)[:, 1]
    threshold = _best_f1_threshold(y_test, y_prob)
    y_pred = (y_prob >= threshold).astype(int)

    frac_pos, mean_pred = calibration_curve(y_test, y_prob, n_bins=10, strategy="uniform")
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()

    importances = dict(zip(FEATURE_NAMES, (float(v) for v in model.feature_importances_)))

    metrics = {
        "roc_auc": float(roc_auc_score(y_test, y_prob)),
        "pr_auc": float(average_precision_score(y_test, y_prob)),
        "brier": float(brier_score_loss(y_test, y_prob)),
        "f1_at_threshold": float(f1_score(y_test, y_pred, zero_division=0)),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "calibration_curve": {
            "mean_predicted": [float(v) for v in mean_pred],
            "fraction_positive": [float(v) for v in frac_pos],
        },
    }

    version = "xgb-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    metadata = {
        "model_version": version,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "horizon_days": horizon_days,
        "feature_names": FEATURE_NAMES,
        "feature_importances": importances,
        "threshold": threshold,
        "n_samples": int(len(dataset.y)),
        "n_positive": dataset.num_positive,
        "n_negative": dataset.num_negative,
        "metrics": metrics,
    }

    model.save_model(str(storage.model_path()))
    storage.save_metadata(metadata)
    logger.info(
        "model trained",
        extra={"version": version, "roc_auc": metrics["roc_auc"], "n": len(dataset.y)},
    )
    return metadata


def main(argv: list[str] | None = None) -> int:
    from app.core.config import settings

    parser = argparse.ArgumentParser(description="Train the SSD failure model.")
    parser.add_argument("--horizon-days", type=int, default=settings.prediction_horizon_days)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--score", action="store_true", help="score the fleet after training")
    args = parser.parse_args(argv)

    configure_logging()
    metadata = train(horizon_days=args.horizon_days, seed=args.seed)
    print(json.dumps({k: metadata[k] for k in ("model_version", "n_samples", "metrics")}, indent=2))

    if args.score:
        from app.ml.score import score_fleet_cli

        score_fleet_cli()
    return 0


if __name__ == "__main__":
    sys.exit(main())
