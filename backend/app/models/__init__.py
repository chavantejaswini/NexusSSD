"""ORM models. Importing this package registers all tables on Base.metadata."""

from app.models.chat import ChatHistory
from app.models.drive import Drive, DriveStatus
from app.models.fleet import Alert, Maintenance, Prediction
from app.models.knowledge import Document, Embedding
from app.models.telemetry import Telemetry

__all__ = [
    "Drive",
    "DriveStatus",
    "Telemetry",
    "Prediction",
    "Maintenance",
    "Alert",
    "Document",
    "Embedding",
    "ChatHistory",
]
