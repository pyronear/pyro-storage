# Copyright (C) 2022-2023, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

from typing import Any, Dict, List

from fastapi import APIRouter, Path, Security, status

from app.api import crud
from app.api.crud.authorizations import check_access_read, is_admin_access
from app.api.deps import get_current_access
from app.api.schemas import AccessType, AnnotationIn, AnnotationOut
from app.db import annotations

router = APIRouter()


async def check_annotation_registration(annotation_id: int) -> Dict[str, Any]:
    """Checks whether the media is registered in the DB"""
    return await crud.get_entry(annotations, annotation_id)


@router.post(
    "/",
    response_model=AnnotationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create an annotation related to a specific media",
)
async def create_annotation(
    payload: AnnotationIn, _=Security(get_current_access, scopes=[AccessType.admin, AccessType.user])
):
    """
    Creates an annotation related to specific media, based on media_id as argument, and with as many observations as needed

    Below, click on "Schema" for more detailed information about arguments
    or "Example Value" to get a concrete idea of arguments
    """
    return await crud.create_entry(annotations, payload)


@router.get("/{annotation_id}/", response_model=AnnotationOut, summary="Get information about a specific annotation")
async def get_annotation(
    annotation_id: int = Path(..., gt=0),
    requester=Security(get_current_access, scopes=[AccessType.admin, AccessType.user]),
):
    """
    Based on a annotation_id, retrieves information about the specified media
    """
    await check_access_read(requester.id)
    return await crud.get_entry(annotations, annotation_id)


@router.get("/", response_model=List[AnnotationOut], summary="Get the list of all annotations")
async def fetch_annotations(
    requester=Security(get_current_access, scopes=[AccessType.admin, AccessType.user]),
):
    """
    Retrieves the list of all annotations and their information
    """
    if await is_admin_access(requester.id):
        return await crud.fetch_all(annotations)
    else:
        return []


@router.put("/{annotation_id}/", response_model=AnnotationOut, summary="Update information about a specific annotation")
async def update_annotation(
    payload: AnnotationIn,
    annotation_id: int = Path(..., gt=0),
    _=Security(get_current_access, scopes=[AccessType.admin]),
):
    """
    Based on a annotation_id, updates information about the specified annotation
    """
    return await crud.update_entry(annotations, payload, annotation_id)


@router.delete("/{annotation_id}/", response_model=AnnotationOut, summary="Delete a specific annotation")
async def delete_annotation(
    annotation_id: int = Path(..., gt=0), _=Security(get_current_access, scopes=[AccessType.admin])
):
    """
    Based on a annotation_id, deletes the specified annotation
    """
    return await crud.delete_entry(annotations, annotation_id)
