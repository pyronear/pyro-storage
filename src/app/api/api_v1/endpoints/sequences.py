# Copyright (C) 2025, Pyronear.

from datetime import datetime
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    Form,
    Path,
    status,
)

from app.api.dependencies import get_sequence_crud
from app.crud import SequenceCRUD
from app.models import Sequence
from app.schemas.sequence import (
    SequenceCreate,
)

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_sequence(
    source_api: str = Form(...),
    alert_api_id: int = Form(...),
    camera_name: str = Form(...),
    organisation: str = Form(...),
    is_wildfire_alertapi: bool = Form(...),
    azimuth: Optional[int] = Form(None),
    created_at: Optional[datetime] = Form(None),
    last_seen_at: Optional[datetime] = Form(None),
    sequences: SequenceCRUD = Depends(get_sequence_crud),
) -> Sequence:
    payload = SequenceCreate(
        source_api=source_api,
        alert_api_id=alert_api_id,
        camera_name=camera_name,
        organisation=organisation,
        is_wildfire_alertapi=is_wildfire_alertapi,
        azimuth=azimuth,
        created_at=created_at or datetime.utcnow(),
        last_seen_at=last_seen_at or datetime.utcnow(),
    )
    return await sequences.create(payload)


@router.get("/")
async def list_sequences(
    sequences: SequenceCRUD = Depends(get_sequence_crud),
) -> List[Sequence]:
    return await sequences.fetch_all()


@router.get("/{sequence_id}")
async def get_sequence(
    sequence_id: int = Path(..., gt=0),
    sequences: SequenceCRUD = Depends(get_sequence_crud),
) -> Sequence:
    return await sequences.get(sequence_id, strict=True)


@router.delete("/{sequence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sequence(
    sequence_id: int = Path(..., gt=0),
    sequences: SequenceCRUD = Depends(get_sequence_crud),
) -> None:
    await sequences.delete(sequence_id)
