# Copyright (C) 2025, Pyronear.

from datetime import datetime
from typing import List
import json
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
from app.schemas.sequence_annotations import SequenceAnnotationCreate, SequenceAnnotationRead, SequenceAnnotationUpdate

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_sequence_annotation(
    sequence_id: int = Form(...),
    has_smoke: bool = Form(...),
    has_false_positives: bool = Form(...),
    has_missed_smoke: bool = Form(...),
    #annotation: str = Form(...),
    processing_stage: SequenceAnnotationProcessingStage = Form(...),
    annotations: SequenceAnnotationCRUD = Depends(get_sequence_annotation_crud),
    false_positive_types: str = Form(...),
) -> SequenceAnnotationRead:
    #parsed_annotation = json.loads(annotation)
    payload = SequenceAnnotationCreate(
        sequence_id=sequence_id,
        has_smoke=has_smoke,
        has_false_positives=has_false_positives,
        has_missed_smoke=has_missed_smoke,
        #annotation=parsed_annotation,
        processing_stage=processing_stage,
        false_positive_types=false_positive_types,
        created_at=datetime.utcnow(),
    )
    return await annotations.create(payload)


@router.get("/")
async def list_sequence_annotations(
    annotations: SequenceAnnotationCRUD = Depends(get_sequence_annotation_crud),
) -> List[SequenceAnnotationRead]:
    return await annotations.fetch_all()


@router.get("/{annotation_id}")
async def get_sequence_annotation(
    annotation_id: int = Path(..., gt=0),
    annotations: SequenceAnnotationCRUD = Depends(get_sequence_annotation_crud),
) -> SequenceAnnotationRead:
    return await annotations.get(annotation_id, strict=True)


@router.patch("/{annotation_id}")
async def update_sequence_annotation(
    annotation_id: int = Path(..., gt=0),
    payload: SequenceAnnotationUpdate = ...,
    annotations: SequenceAnnotationCRUD = Depends(get_sequence_annotation_crud),
) -> SequenceAnnotationRead:
    updated_payload = payload.copy(update={"updated_at": datetime.utcnow()})
    return await annotations.update(annotation_id, updated_payload)


@router.delete("/{annotation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sequence_annotation(
    annotation_id: int = Path(..., gt=0),
    annotations: SequenceAnnotationCRUD = Depends(get_sequence_annotation_crud),
) -> None:
    await annotations.delete(annotation_id)
