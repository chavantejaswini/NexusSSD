"""Model artifact storage — resolves paths and reads/writes metadata.

Artifacts live in `<repo>/ml/artifacts/` by default (configurable via
MODEL_ARTIFACT_DIR). A relative dir is resolved against the repository root so
the location is stable regardless of the current working directory.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings

# backend/app/ml/storage.py -> parents[3] == repository root (NexusSSD/)
_REPO_ROOT = Path(__file__).resolve().parents[3]

MODEL_FILENAME = "model.json"
METADATA_FILENAME = "metadata.json"


def artifact_dir() -> Path:
    path = Path(settings.model_artifact_dir)
    if not path.is_absolute():
        path = _REPO_ROOT / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def model_path() -> Path:
    return artifact_dir() / MODEL_FILENAME


def metadata_path() -> Path:
    return artifact_dir() / METADATA_FILENAME


def model_exists() -> bool:
    return model_path().exists() and metadata_path().exists()


def save_metadata(metadata: dict) -> None:
    metadata_path().write_text(json.dumps(metadata, indent=2))


def load_metadata() -> dict:
    return json.loads(metadata_path().read_text())
