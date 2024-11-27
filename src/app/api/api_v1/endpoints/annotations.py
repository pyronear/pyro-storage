# Copyright (C) 2022-2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

from fastapi import (
    APIRouter,
    Depends,
    Form,
    Security,
    status,
)

from app.api.dependencies import (
    get_annotation_crud,
    get_jwt,
)
from app.crud import AnnotationCRUD
from app.models import Annotation, Label, Role
from app.schemas.annotations import AnnotationCreate
from app.schemas.login import TokenPayload

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Register a new annotation detection")
async def create_annotation(
    gif_url: str = Form(...),
    label: Label = Form(...),
    annotations: AnnotationCRUD = Depends(get_annotation_crud),
    _token_payload: TokenPayload = Security(get_jwt, scopes=[Role.ADMIN, Role.USER, Role.AGENT]),
) -> Annotation:
    return await annotations.create(AnnotationCreate(gif_url=gif_url, label=label))
