# Copyright (C) 2020-2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from datetime import datetime
from typing import List, cast

from fastapi import APIRouter, Depends, File, HTTPException, Path, Security, UploadFile, status

from app.api.dependencies import get_jwt, get_source_crud
from app.core.config import settings
from app.core.security import create_access_token
from app.crud import SourceCRUD
from app.models import Role, Source, UserRole
from app.schemas.login import Token, TokenPayload
from app.schemas.sources import LastActive, LastImage, SourceCreate
from app.services.storage import s3_service, upload_file

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Register a new camera")
async def register_source(
    payload: SourceCreate,
    sources: SourceCRUD = Depends(get_source_crud),
    token_payload: TokenPayload = Security(get_jwt, scopes=[UserRole.ADMIN, UserRole.AGENT]),
) -> Source:
    if token_payload._id != payload._id and UserRole.ADMIN not in token_payload.scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden.")
    return await sources.create(payload)


@router.get("/{camera_id}", status_code=status.HTTP_200_OK, summary="Fetch the information of a specific source")
async def get_source(
    camera_id: int = Path(..., gt=0),
    sources: SourceCRUD = Depends(get_source_crud),
    token_payload: TokenPayload = Security(get_jwt, scopes=[UserRole.ADMIN, UserRole.AGENT, UserRole.USER]),
) -> Source:
    camera = cast(Source, await sources.get(camera_id, strict=True))
    if token_payload._id != camera._id and UserRole.ADMIN not in token_payload.scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden.")
    return camera


@router.get("/", status_code=status.HTTP_200_OK, summary="Fetch all the sources")
async def fetch_sources(
    sources: SourceCRUD = Depends(get_source_crud),
    token_payload: TokenPayload = Security(get_jwt, scopes=[UserRole.ADMIN, UserRole.AGENT, UserRole.USER]),
) -> List[Source]:
    all_sources = [elt for elt in await sources.fetch_all()]
    if UserRole.ADMIN in token_payload.scopes:
        return all_sources
    return [camera for camera in all_sources if camera._id == token_payload._id]


@router.patch("/heartbeat", status_code=status.HTTP_200_OK, summary="Update last ping of a source")
async def heartbeat(
    sources: SourceCRUD = Depends(get_source_crud),
    token_payload: TokenPayload = Security(get_jwt, scopes=[Role.CAMERA]),
) -> Source:
    return await sources.update(token_payload.sub, LastActive(last_active_at=datetime.utcnow()))


@router.patch("/image", status_code=status.HTTP_200_OK, summary="Update last image of a source")
async def update_image(
    file: UploadFile = File(..., alias="file"),
    sources: SourceCRUD = Depends(get_source_crud),
    token_payload: TokenPayload = Security(get_jwt, scopes=[Role.CAMERA]),
) -> Source:
    bucket_key = await upload_file(file, token_payload._id, token_payload.sub)
    # If the upload succeeds, delete the previous image
    cam = cast(Source, await sources.get(token_payload.sub, strict=True))
    if isinstance(cam.last_image, str):
        s3_service.get_bucket(s3_service.resolve_bucket_name(token_payload._id)).delete_file(cam.last_image)
    # Update the DB entry
    return await sources.update(token_payload.sub, LastImage(last_image=bucket_key, last_active_at=datetime.utcnow()))


@router.post("/{source_id}/token", status_code=status.HTTP_200_OK, summary="Request an access token for the source")
async def create_source_token(
    source_id: int = Path(..., gt=0),
    sources: SourceCRUD = Depends(get_source_crud),
    token_payload: TokenPayload = Security(get_jwt, scopes=[UserRole.ADMIN]),
) -> Token:
    camera = cast(Source, await sources.get(source_id, strict=True))
    # create access token using user user_id/user_scopes
    token_data = {"sub": str(source_id), "scopes": ["camera"], "_id": camera._id}
    token = create_access_token(token_data, settings.JWT_UNLIMITED)
    return Token(access_token=token, token_type="bearer")  # noqa S106


@router.delete("/{camera_id}", status_code=status.HTTP_200_OK, summary="Delete a camera")
async def delete_source(
    source_id: int = Path(..., gt=0),
    sources: SourceCRUD = Depends(get_source_crud),
    token_payload: TokenPayload = Security(get_jwt, scopes=[UserRole.ADMIN]),
) -> None:
    await sources.delete(source_id)
