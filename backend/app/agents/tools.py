"""Tools the agents call — all bound to a single DB session.

The SQL tool intentionally does *not* execute free-form model-generated SQL.
Instead it maps the user's intent to a small set of safe, parameterized,
read-only queries over allowlisted tables — the "SQL reasoning" agent with
guardrails. Each result includes a human-readable SQL string for the trace.
"""

from __future__ import annotations

import re

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.drive import Drive, DriveStatus
from app.models.fleet import Alert, Prediction
from app.models.telemetry import Telemetry
from app.services import prediction_service, rag_service

_SERIAL_RE = re.compile(r"\b(NX-\d{4,6})\b", re.IGNORECASE)
_DRIVE_ID_RE = re.compile(r"\bdrive\s+#?(\d+)\b", re.IGNORECASE)
_TOPN_RE = re.compile(r"\btop\s+(\d{1,3})\b", re.IGNORECASE)


def _top_n(query: str, default: int = 5) -> int:
    match = _TOPN_RE.search(query)
    return min(int(match.group(1)), 50) if match else default


class Tools:
    def __init__(self, session: Session) -> None:
        self.session = session

    # ---- SQL reasoning (intent -> safe query) ----
    def sql(self, query: str) -> dict:
        q = query.lower()
        limit = _top_n(query)
        if "alert" in q:
            return self._alerts(limit)
        if "hot" in q or "temperature" in q or "temp" in q:
            return self._hottest(limit)
        if "failed" in q or "failure" in q or "dead" in q:
            return self._by_status(DriveStatus.FAILED.value)
        if any(k in q for k in ("risk", "likely", "fail", "predict", "probability")):
            return self._top_risk(limit)
        return self._fleet_summary()

    def _fleet_summary(self) -> dict:
        rows = self.session.execute(
            select(Drive.status, func.count()).group_by(Drive.status)
        ).all()
        by_status = {status: count for status, count in rows}
        total = sum(by_status.values())
        return {
            "intent": "fleet_summary",
            "sql": "SELECT status, COUNT(*) FROM drives GROUP BY status",
            "rows": [{"metric": "total_drives", "value": total}]
            + [{"metric": f"status_{s}", "value": c} for s, c in by_status.items()],
        }

    def _by_status(self, status: str) -> dict:
        count = self.session.execute(
            select(func.count()).select_from(Drive).where(Drive.status == status)
        ).scalar_one()
        drives = self.session.execute(
            select(Drive.serial_number, Drive.model).where(Drive.status == status).limit(20)
        ).all()
        return {
            "intent": "drives_by_status",
            "sql": f"SELECT serial_number, model FROM drives WHERE status = '{status}'",
            "rows": [{"count": count}]
            + [{"serial_number": s, "model": m} for s, m in drives],
        }

    def _hottest(self, limit: int) -> dict:
        # Latest telemetry row per drive, ordered by temperature desc.
        latest_date = (
            select(Telemetry.drive_id, func.max(Telemetry.date).label("d"))
            .group_by(Telemetry.drive_id)
            .subquery()
        )
        rows = self.session.execute(
            select(Drive.serial_number, Telemetry.temperature, Telemetry.date)
            .join(Telemetry, Telemetry.drive_id == Drive.id)
            .join(
                latest_date,
                (latest_date.c.drive_id == Telemetry.drive_id)
                & (latest_date.c.d == Telemetry.date),
            )
            .order_by(desc(Telemetry.temperature))
            .limit(limit)
        ).all()
        return {
            "intent": "hottest_drives",
            "sql": "SELECT serial_number, temperature FROM telemetry (latest per drive) "
            "ORDER BY temperature DESC",
            "rows": [
                {"serial_number": s, "temperature": t, "date": str(d)} for s, t, d in rows
            ],
        }

    def _alerts(self, limit: int) -> dict:
        rows = self.session.execute(
            select(Drive.serial_number, Alert.severity, Alert.message)
            .join(Drive, Drive.id == Alert.drive_id)
            .where(Alert.acknowledged.is_(False))
            .order_by(desc(Alert.created_at))
            .limit(limit)
        ).all()
        return {
            "intent": "open_alerts",
            "sql": "SELECT serial_number, severity, message FROM alerts "
            "WHERE acknowledged = false ORDER BY created_at DESC",
            "rows": [
                {"serial_number": s, "severity": sev, "message": msg} for s, sev, msg in rows
            ],
        }

    def _top_risk(self, limit: int) -> dict:
        # Latest prediction per drive, ordered by probability desc.
        latest = (
            select(Prediction.drive_id, func.max(Prediction.predicted_at).label("t"))
            .group_by(Prediction.drive_id)
            .subquery()
        )
        rows = self.session.execute(
            select(Drive.serial_number, Prediction.failure_probability, Prediction.horizon_days)
            .join(Prediction, Prediction.drive_id == Drive.id)
            .join(
                latest,
                (latest.c.drive_id == Prediction.drive_id)
                & (latest.c.t == Prediction.predicted_at),
            )
            .order_by(desc(Prediction.failure_probability))
            .limit(limit)
        ).all()
        return {
            "intent": "top_risk",
            "sql": "SELECT serial_number, failure_probability FROM predictions "
            "(latest per drive) ORDER BY failure_probability DESC",
            "rows": [
                {"serial_number": s, "failure_probability": round(p, 4), "horizon_days": h}
                for s, p, h in rows
            ],
        }

    # ---- Prediction agent ----
    def prediction(self, query: str) -> dict:
        drive = self._resolve_drive(query)
        try:
            if drive is not None:
                result = prediction_service.predict_for_drive(self.session, drive.id)
                return {"mode": "single", "drive": drive.serial_number, "result": result}
            # No specific drive -> summarize highest-risk from stored predictions.
            return {"mode": "fleet", **self._top_risk(_top_n(query))}
        except prediction_service.ModelNotTrainedError as exc:
            return {"mode": "unavailable", "note": str(exc)}
        except prediction_service.DriveHasNoTelemetryError as exc:
            return {"mode": "unavailable", "note": str(exc)}

    def _resolve_drive(self, query: str) -> Drive | None:
        serial_match = _SERIAL_RE.search(query)
        if serial_match:
            return self.session.execute(
                select(Drive).where(
                    func.upper(Drive.serial_number) == serial_match.group(1).upper()
                )
            ).scalars().first()
        id_match = _DRIVE_ID_RE.search(query)
        if id_match:
            return self.session.get(Drive, int(id_match.group(1)))
        return None

    # ---- RAG agent ----
    def rag(self, query: str, top_k: int = 3) -> list[dict]:
        hits = rag_service.retrieve(self.session, query, top_k=top_k)
        return [
            {
                "chunk_text": h.chunk_text,
                "score": round(h.score, 4),
                "source": h.source,
                "document_title": h.document_title,
            }
            for h in hits
        ]
