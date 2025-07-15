# Copyright (C) 2025, Pyronear.

from datetime import datetime
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    Form,
    Path,
    status,
)

from app.api.dependencies import get_sequence_annotation_crud
from app.crud import SequenceAnnotationCRUD
from app.models import SequenceAnnotationProcessingStage
from app.schemas.sequence_annotations import SequenceAnnotationCreate, SequenceAnnotationUpdate

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_sequence_annotation(
    sequence_id: int = Form(...),
    has_smoke: bool = Form(...),
    has_false_positives: bool = Form(...),
    has_missed_smoke: bool = Form(...),
    sequence_bbox_predictions_annotation: str = Form(...),
    sequence_stage: SequenceAnnotationProcessingStage = Form(...),
    annotations: SequenceAnnotationCRUD = Depends(get_sequence_annotation_crud),
) -> SequenceAnnotationCreate:
    payload = SequenceAnnotationCreate(
        sequence_id=sequence_id,
        has_smoke=has_smoke,
        has_false_positives=has_false_positives,
        has_missed_smoke=has_missed_smoke,
        sequence_bbox_predictions_annotation=sequence_bbox_predictions_annotation,
        sequence_stage=sequence_stage,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    return await annotations.create(payload)


@router.get("/")
async def list_sequence_annotations(
    annotations: SequenceAnnotationCRUD = Depends(get_sequence_annotation_crud),
) -> List[SequenceAnnotationCreate]:
    return await annotations.fetch_all()


@router.get("/{annotation_id}")
async def get_sequence_annotation(
    annotation_id: int = Path(..., gt=0),
    annotations: SequenceAnnotationCRUD = Depends(get_sequence_annotation_crud),
) -> SequenceAnnotationCreate:
    return await annotations.get(annotation_id, strict=True)


@router.patch("/{annotation_id}")
async def update_sequence_annotation(
    annotation_id: int = Path(..., gt=0),
    payload: SequenceAnnotationUpdate = ...,
    annotations: SequenceAnnotationCRUD = Depends(get_sequence_annotation_crud),
) -> SequenceAnnotationUpdate:
    return await annotations.update(annotation_id, payload)


@router.delete("/{annotation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sequence_annotation(
    annotation_id: int = Path(..., gt=0),
    annotations: SequenceAnnotationCRUD = Depends(get_sequence_annotation_crud),
) -> None:
    await annotations.delete(annotation_id)
