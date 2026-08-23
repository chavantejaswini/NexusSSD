"""Failure-prediction endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.prediction import PredictRequest, PredictResponse
from app.services import prediction_service
from app.services.prediction_service import (
    DriveHasNoTelemetryError,
    InvalidFeaturesError,
    ModelNotTrainedError,
)

router = APIRouter(tags=["predictions"])


@router.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest, db: Session = Depends(get_db)) -> PredictResponse:
    try:
        if request.drive_id is not None:
            result = prediction_service.predict_for_drive(db, request.drive_id)
            if result is None:
                raise HTTPException(status_code=404, detail=f"drive {request.drive_id} not found")
        else:
            assert request.features is not None  # guaranteed by schema validator
            result = prediction_service.predict_from_features(request.features)
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except InvalidFeaturesError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except DriveHasNoTelemetryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return PredictResponse.model_validate(result)
