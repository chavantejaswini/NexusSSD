"""CLI to score the whole fleet, writing predictions and alerts.

    python -m app.ml.score
"""

from __future__ import annotations

import json
import sys

from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.services import prediction_service


def score_fleet_cli() -> dict:
    session = SessionLocal()
    try:
        stats = prediction_service.score_fleet(session)
    finally:
        session.close()
    payload = {
        "scored": stats.scored,
        "skipped_no_telemetry": stats.skipped_no_telemetry,
        "alerts_created": stats.alerts_created,
    }
    print(json.dumps(payload, indent=2))
    return payload


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    score_fleet_cli()
    return 0


if __name__ == "__main__":
    sys.exit(main())
