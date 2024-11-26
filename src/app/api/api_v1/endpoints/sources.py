# Copyright (C) 2020-2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from datetime import datetime
from typing import List, cast

from fastapi import APIRouter, Depends, HTTPException, Path, Security, status

from app.api.dependencies import get_jwt, get_source_crud
from app.core.config import settings
from app.core.security import create_access_token
from app.crud import SourceCRUD
from app.models import Role, Source, UserRole
from app.schemas.login import Token, TokenPayload
from app.schemas.sources import LastActive, SourceCreate
from app.services.storage import s3_service

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Register a new source")
async def register_source(
    payload: SourceCreate,
    sources: SourceCRUD = Depends(get_source_crud),
    token_payload: TokenPayload = Security(get_jwt, scopes=[UserRole.ADMIN, UserRole.AGENT]),
) -> Source:
    if UserRole.ADMIN not in token_payload.scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden.")

    source = await sources.create(payload)
    bucket_name = s3_service.resolve_bucket_name(source.id)
    if not s3_service.create_bucket(bucket_name):
        # Delete the organization if the bucket creation failed
        await sources.delete(source.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create bucket")
    return source


@router.get("/{source_id}", status_code=status.HTTP_200_OK, summary="Fetch the information of a specific source")
async def get_source(
    source_id: int = Path(..., gt=0),
    sources: SourceCRUD = Depends(get_source_crud),
    token_payload: TokenPayload = Security(get_jwt, scopes=[UserRole.ADMIN, UserRole.AGENT, UserRole.USER]),
) -> Source:
    source = cast(Source, await sources.get(source_id, strict=True))
    if token_payload.source_id != source_id and UserRole.ADMIN not in token_payload.scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden.")
    return source


@router.get("/", status_code=status.HTTP_200_OK, summary="Fetch all the sources")
async def fetch_sources(
    sources: SourceCRUD = Depends(get_source_crud),
    token_payload: TokenPayload = Security(get_jwt, scopes=[UserRole.ADMIN, UserRole.AGENT, UserRole.USER]),
) -> List[Source]:
    all_sources = [elt for elt in await sources.fetch_all()]
    if UserRole.ADMIN in token_payload.scopes:
        return all_sources
    return [source for source in all_sources if source.id == token_payload.source_id]


@router.patch("/heartbeat", status_code=status.HTTP_200_OK, summary="Update last ping of a source")
async def heartbeat(
    sources: SourceCRUD = Depends(get_source_crud),
    token_payload: TokenPayload = Security(get_jwt, scopes=[Role.AGENT]),
) -> Source:
    return await sources.update(token_payload.sub, LastActive(last_active_at=datetime.utcnow()))


@router.post("/{source_id}/token", status_code=status.HTTP_200_OK, summary="Request an access token for the source")
async def create_source_token(
    source_id: int = Path(..., gt=0),
    sources: SourceCRUD = Depends(get_source_crud),
    _token_payload: TokenPayload = Security(get_jwt, scopes=[UserRole.ADMIN]),
) -> Token:
    source = cast(Source, await sources.get(source_id, strict=True))
    # create access token using user user_id/user_scopes
    token_data = {"sub": str(source_id), "scopes": ["agent"], "source_id": source.id}
    token = create_access_token(token_data, settings.JWT_UNLIMITED)
    return Token(access_token=token, token_type="bearer")  # noqa S106


@router.delete("/{source_id}", status_code=status.HTTP_200_OK, summary="Delete a source")
async def delete_source(
    source_id: int = Path(..., gt=0),
    sources: SourceCRUD = Depends(get_source_crud),
    _token_payload: TokenPayload = Security(get_jwt, scopes=[UserRole.ADMIN]),
) -> None:
    await sources.delete(source_id)
