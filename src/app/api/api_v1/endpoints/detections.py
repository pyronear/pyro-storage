# Copyright (C) 2024, Pyronear.

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Path,
    Query,
    UploadFile,
    status,
)
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import get_detection_crud
from app.crud import DetectionCRUD
from app.db import get_session
from app.models import Detection
from app.schemas.detection import (
    DetectionCreate,
    DetectionUrl,
    DetectionWithUrl,
)
from app.services.storage import s3_service, upload_file

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Register a new wildfire detection")
async def create_detection(
    algo_predictions: Dict,
    sequence_id: int,
    file: UploadFile = File(..., alias="file"),
    detections: DetectionCRUD = Depends(get_detection_crud),
) -> Detection:
    # Upload image to S3
    bucket_key = await upload_file(file, bucket_id="default")  # You can change 'default' if bucket logic changes

    # Create detection in DB
    payload = DetectionCreate(
        sequence_id=sequence_id,
        bucket_key=bucket_key,
        algo_predictions=algo_predictions,
    )
    return await detections.create(payload)


@router.get("/{detection_id}")
async def get_detection(
    detection_id: int = Path(..., gt=0),
    detections: DetectionCRUD = Depends(get_detection_crud),
) -> Detection:
    return await detections.get(detection_id, strict=True)


@router.get("/{detection_id}/url", response_model=DetectionUrl)
async def get_detection_url(
    detection_id: int = Path(..., gt=0),
    session: AsyncSession = Depends(get_session),
) -> DetectionUrl:
    detection = await session.get(Detection, detection_id)
    if detection is None:
        raise HTTPException(status_code=404, detail="Detection not found")

    bucket = s3_service.get_bucket("default")  # Use your bucket naming convention here
    return DetectionUrl(url=bucket.get_public_url(detection.bucket_key))


@router.get("/")
async def list_detections(
    detections: DetectionCRUD = Depends(get_detection_crud),
) -> List[Detection]:
    return await detections.fetch_all()


@router.get("/unlabeled/fromdate", response_model=List[DetectionWithUrl])
async def fetch_unlabeled_detections(
    from_date: datetime = Query(...),
    limit: Optional[int] = Query(15),
    offset: Optional[int] = Query(0),
    session: AsyncSession = Depends(get_session),
) -> List[DetectionWithUrl]:
    # This example assumes there's an annotation relation to filter "unlabeled"
    # You may need to adapt based on your annotation schema
    stmt = select(Detection).where(Detection.created_at >= from_date).limit(limit).offset(offset)
    results = (await session.exec(stmt)).all()
    bucket = s3_service.get_bucket("default")
    return [
        DetectionWithUrl(**detection.model_dump(), url=bucket.get_public_url(detection.bucket_key))
        for detection in results
    ]


@router.delete("/{detection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_detection(
    detection_id: int = Path(..., gt=0),
    detections: DetectionCRUD = Depends(get_detection_crud),
) -> None:
    detection = await detections.get(detection_id, strict=True)
    bucket = s3_service.get_bucket("default")
    bucket.delete_file(detection.bucket_key)
    await detections.delete(detection_id)
