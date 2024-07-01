# Copyright (C) 2023-2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

from typing import List

from fastapi import APIRouter, Path, Security, status

from app.api import crud
from app.api.deps import get_current_access
from app.api.schemas import AccessAuth, AccessRead, AccessType, Cred
from app.db import accesses

router = APIRouter()


@router.post("/", response_model=AccessRead, status_code=status.HTTP_201_CREATED, summary="Create an access")
async def create_access(payload: AccessAuth, _=Security(get_current_access, scopes=[AccessType.admin])):
    """
    Creates an annotation related to specific media, based on media_id as argument

    Below, click on "Schema" for more detailed information about arguments
    or "Example Value" to get a concrete idea of arguments
    """
    return await crud.accesses.post_access(accesses, **payload.dict())


@router.get("/{access_id}/", response_model=AccessRead, summary="Get information about a specific access")
async def get_access(access_id: int = Path(..., gt=0), _=Security(get_current_access, scopes=[AccessType.admin])):
    """
    Based on a access_id, retrieves information about the specified access
    """
    entry = await crud.get_entry(accesses, access_id)
    return AccessRead(**entry)


@router.get("/", response_model=List[AccessRead], summary="Get the list of all accesses")
async def fetch_accesses(_=Security(get_current_access, scopes=[AccessType.admin])):
    """
    Retrieves the list of all accesses and their information
    """
    entries = await crud.fetch_all(accesses)
    return [AccessRead(**entry) for entry in entries]


@router.put("/{access_id}/", response_model=None, summary="Update information about a specific access")
async def update_access_pwd(
    payload: Cred, access_id: int = Path(..., gt=0), _=Security(get_current_access, scopes=[AccessType.admin])
):
    """
    Based on a access_id, updates information about the specified access
    """
    await crud.accesses.update_access_pwd(accesses, payload, access_id)


@router.delete("/{access_id}/", response_model=AccessRead, summary="Delete a specific access")
async def delete_access(access_id: int = Path(..., gt=0), _=Security(get_current_access, scopes=[AccessType.admin])):
    """
    Based on a access_id, deletes the specified access
    """
    entry = await crud.delete_entry(accesses, access_id)
    return AccessRead(**entry)
