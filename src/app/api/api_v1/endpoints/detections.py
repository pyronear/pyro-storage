# Copyright (C) 2024, Pyronear.

import json
from datetime import datetime
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Path,
    UploadFile,
    status,
)
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import get_detection_crud
from app.crud import DetectionCRUD
from app.db import get_session
from app.models import Detection
from app.schemas.detection import (
    DetectionCreate,
    DetectionRead,
    DetectionUrl,
)
from app.services.storage import s3_service, upload_file

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Register a new wildfire detection")
async def create_detection(
    algo_predictions: str = Form(...),
    alert_api_id: int = Form(...),
    sequence_id: int = Form(...),
    recorded_at: datetime = Form(),
    file: UploadFile = File(..., alias="file"),
    detections: DetectionCRUD = Depends(get_detection_crud),
) -> DetectionRead:
    # Parse string JSON -> dict
    parsed_predictions = json.loads(algo_predictions)

    # Upload image to S3
    bucket_key = await upload_file(file)

    # Create detection in DB
    payload = DetectionCreate(
        sequence_id=sequence_id,
        alert_api_id=alert_api_id,
        recorded_at=recorded_at,
        bucket_key=bucket_key,
        algo_predictions=parsed_predictions,
    )
    return await detections.create(payload)


@router.get("/{detection_id}")
async def get_detection(
    detection_id: int = Path(..., gt=0),
    detections: DetectionCRUD = Depends(get_detection_crud),
) -> DetectionRead:
    return await detections.get(detection_id, strict=True)


@router.get("/{detection_id}/url", response_model=DetectionUrl)
async def get_detection_url(
    detection_id: int = Path(..., gt=0),
    session: AsyncSession = Depends(get_session),
) -> DetectionUrl:
    detection = await session.get(Detection, detection_id)
    if detection is None:
        raise HTTPException(status_code=404, detail="Detection not found")

    bucket = s3_service.get_bucket(s3_service.resolve_bucket_name())  # Use your bucket naming convention here
    return DetectionUrl(url=bucket.get_public_url(detection.bucket_key))


@router.get("/")
async def list_detections(
    detections: DetectionCRUD = Depends(get_detection_crud),
) -> List[DetectionRead]:
    return await detections.fetch_all()


@router.delete("/{detection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_detection(
    detection_id: int = Path(..., gt=0),
    detections: DetectionCRUD = Depends(get_detection_crud),
) -> None:
    detection = await detections.get(detection_id, strict=True)
    bucket = s3_service.get_bucket(s3_service.resolve_bucket_name())
    bucket.delete_file(detection.bucket_key)
    await detections.delete(detection_id)
