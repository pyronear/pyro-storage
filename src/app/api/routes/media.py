# Copyright (C) 2022, Pyronear.

# This program is licensed under the Apache License version 2.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0.txt> for full license details.

from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Path, Security, UploadFile, status

from app.api import crud
from app.api.crud.authorizations import check_access_read, is_admin_access
from app.api.deps import get_current_access
from app.api.schemas import AccessType, MediaCreation, MediaIn, MediaOut, MediaUrl
from app.api.security import hash_content_file
from app.db import get_session, media
from app.services import media_bucket, resolve_bucket_key

router = APIRouter()


async def check_media_registration(media_id: int) -> Dict[str, Any]:
    """Checks whether the media is registered in the DB"""
    return await crud.get_entry(media, media_id)


@router.post(
    "/",
    response_model=MediaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a media related to a specific device",
)
async def create_media(payload: MediaIn, _=Security(get_current_access, scopes=[AccessType.admin])):
    """
    Creates a media related to specific device, based on device_id as argument

    Below, click on "Schema" for more detailed information about arguments
    or "Example Value" to get a concrete idea of arguments
    """
    return await crud.create_entry(media, payload)


@router.get("/{media_id}/", response_model=MediaOut, summary="Get information about a specific media")
async def get_media(
    media_id: int = Path(..., gt=0), requester=Security(get_current_access, scopes=[AccessType.admin, AccessType.user])
):
    """
    Based on a media_id, retrieves information about the specified media
    """
    await check_access_read(requester.id)

    return await crud.get_entry(media, media_id)


@router.get("/", response_model=List[MediaOut], summary="Get the list of all media")
async def fetch_media(
    requester=Security(get_current_access, scopes=[AccessType.admin, AccessType.user]), session=Depends(get_session)
):
    """
    Retrieves the list of all media and their information
    """
    if await is_admin_access(requester.id):
        return await crud.fetch_all(media)
    return []


@router.put("/{media_id}/", response_model=MediaOut, summary="Update information about a specific media")
async def update_media(
    payload: MediaIn, media_id: int = Path(..., gt=0), _=Security(get_current_access, scopes=[AccessType.admin])
):
    """
    Based on a media_id, updates information about the specified media
    """
    return await crud.update_entry(media, payload, media_id)


@router.delete("/{media_id}/", response_model=MediaOut, summary="Delete a specific media")
async def delete_media(media_id: int = Path(..., gt=0), _=Security(get_current_access, scopes=[AccessType.admin])):
    """
    Based on a media_id, deletes the specified media
    """
    return await crud.delete_entry(media, media_id)


@router.post("/{media_id}/upload", response_model=MediaOut, status_code=200)
async def upload_media(
    background_tasks: BackgroundTasks,
    media_id: int = Path(..., gt=0),
    file: UploadFile = File(...),
):
    """
    Upload a media (image or video) linked to an existing media object in the DB
    """

    # Check in DB
    entry = await check_media_registration(media_id)

    # Concatenate the first 32 chars (to avoid system interactions issues) of SHA256 hash with file extension
    file_hash = hash_content_file(file.file.read())
    file_name = f"{file_hash[:32]}.{file.filename.rpartition('.')[-1]}"
    # Reset byte position of the file (cf. https://fastapi.tiangolo.com/tutorial/request-files/#uploadfile)
    await file.seek(0)
    # If files are in a subfolder of the bucket, prepend the folder path
    bucket_key = resolve_bucket_key(file_name, media_bucket.folder)

    # Upload if bucket_key is different (otherwise the content is the exact same)
    if isinstance(entry["bucket_key"], str) and entry["bucket_key"] == bucket_key:
        return await crud.get_entry(media, media_id)
    else:
        # Failed upload
        if not await media_bucket.upload_file(bucket_key=bucket_key, file_binary=file.file):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed upload")
        # Data integrity check
        uploaded_file = await media_bucket.get_file(bucket_key=bucket_key)
        # Failed download
        if uploaded_file is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="The data integrity check failed (unable to download media from bucket)",
            )
        # Remove temp local file
        background_tasks.add_task(media_bucket.flush_tmp_file, uploaded_file)
        # Check the hash
        with open(uploaded_file, "rb") as f:
            upload_hash = hash_content_file(f.read())
        if upload_hash != file_hash:
            # Delete corrupted file
            await media_bucket.delete_file(bucket_key)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Data was corrupted during upload"
            )

        entry_dict = dict(**entry)
        entry_dict["bucket_key"] = bucket_key
        return await crud.update_entry(media, MediaCreation(**entry_dict), media_id)


@router.get("/{media_id}/url", response_model=MediaUrl, status_code=200)
async def get_media_url(
    media_id: int = Path(..., gt=0), requester=Security(get_current_access, scopes=[AccessType.admin, AccessType.user])
):
    """Resolve the temporary media image URL"""
    await check_access_read(requester.id)

    # Check in DB
    media_instance = await check_media_registration(media_id)
    # Check in bucket
    temp_public_url = await media_bucket.get_public_url(media_instance["bucket_key"])
    return MediaUrl(url=temp_public_url)
