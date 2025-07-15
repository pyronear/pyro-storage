# Copyright (C) 2025, Pyronear.

import json
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Form, Path, status

from app.api.dependencies import get_detection_annotation_crud
from app.crud import DetectionAnnotationCRUD
from app.models import DetectionAnnotationProcessingStage
from app.schemas.detection_annotations import (
    DetectionAnnotationCreate,
    DetectionAnnotationRead,
    DetectionAnnotationUpdate,
)

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_detection_annotation(
    detection_id: int = Form(...),
    source_api: str = Form(...),
    alert_api_id: int = Form(...),
    annotation: str = Form(..., description="JSON string of annotation object"),
    processing_stages: DetectionAnnotationProcessingStage = Form(
        ..., description="JSON string tracking annotation stages"
    ),
    annotations: DetectionAnnotationCRUD = Depends(get_detection_annotation_crud),
) -> DetectionAnnotationRead:
    parsed_annotation = json.loads(annotation)
    payload = DetectionAnnotationCreate(
        detection_id=detection_id,
        source_api=source_api,
        alert_api_id=alert_api_id,
        annotation=parsed_annotation,
        processing_stages=processing_stages,
        created_at=datetime.utcnow(),
    )
    return await annotations.create(payload)


@router.get("/")
async def list_annotations(
    annotations: DetectionAnnotationCRUD = Depends(get_detection_annotation_crud),
) -> List[DetectionAnnotationRead]:
    return await annotations.fetch_all()


@router.get("/{annotation_id}")
async def get_annotation(
    annotation_id: int = Path(..., gt=0),
    annotations: DetectionAnnotationCRUD = Depends(get_detection_annotation_crud),
) -> DetectionAnnotationRead:
    return await annotations.get(annotation_id, strict=True)


@router.patch("/{annotation_id}")
async def update_annotation(
    annotation_id: int = Path(..., gt=0),
    payload: DetectionAnnotationUpdate = ...,
    annotations: DetectionAnnotationCRUD = Depends(get_detection_annotation_crud),
) -> DetectionAnnotationRead:
    updated_payload = payload.copy(update={"updated_at": datetime.utcnow()})
    return await annotations.update(annotation_id, updated_payload)


@router.delete("/{annotation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_annotation(
    annotation_id: int = Path(..., gt=0),
    annotations: DetectionAnnotationCRUD = Depends(get_detection_annotation_crud),
) -> None:
    await annotations.delete(annotation_id)
