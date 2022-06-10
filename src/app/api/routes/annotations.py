# Copyright (C) 2022, Pyronear.

# This program is licensed under the Apache License version 2.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0.txt> for full license details.

from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Path, Security, UploadFile, status

from app.api import crud
from app.api.crud.authorizations import check_access_read, is_admin_access
from app.api.deps import get_current_access
from app.api.schemas import AccessType, AnnotationCreation, AnnotationIn, AnnotationOut, AnnotationUrl
from app.api.security import hash_content_file
from app.db import annotations
from app.services import annotations_bucket, resolve_bucket_key

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
    Creates an annotation related to specific media, based on media_id as argument

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


@router.post("/{annotation_id}/upload", response_model=AnnotationOut, status_code=200)
async def upload_annotation(
    background_tasks: BackgroundTasks,
    annotation_id: int = Path(..., gt=0),
    file: UploadFile = File(...),
):
    """
    Upload a annotation (image or video) linked to an existing annotation object in the DB
    """

    # Check in DB
    entry = await check_annotation_registration(annotation_id)

    # Concatenate the first 32 chars (to avoid system interactions issues) of SHA256 hash with file extension
    file_hash = hash_content_file(file.file.read())
    file_name = f"{file_hash[:32]}.{file.filename.rpartition('.')[-1]}"
    # Reset byte position of the file (cf. https://fastapi.tiangolo.com/tutorial/request-files/#uploadfile)
    await file.seek(0)
    # If files are in a subfolder of the bucket, prepend the folder path
    bucket_key = resolve_bucket_key(file_name, annotations_bucket.folder)

    # Upload if bucket_key is different (otherwise the content is the exact same)
    if isinstance(entry["bucket_key"], str) and entry["bucket_key"] == bucket_key:
        return await crud.get_entry(annotations, annotation_id)
    else:
        # Failed upload
        if not await annotations_bucket.upload_file(bucket_key=bucket_key, file_binary=file.file):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed upload")
        # Data integrity check
        uploaded_file = await annotations_bucket.get_file(bucket_key=bucket_key)
        # Failed download
        if uploaded_file is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="The data integrity check failed (unable to download media from bucket)",
            )
        # Remove temp local file
        background_tasks.add_task(annotations_bucket.flush_tmp_file, uploaded_file)
        # Check the hash
        with open(uploaded_file, "rb") as f:
            upload_hash = hash_content_file(f.read())
        if upload_hash != file_hash:
            # Delete corrupted file
            await annotations_bucket.delete_file(bucket_key)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Data was corrupted during upload"
            )

        entry_dict = dict(**entry)
        entry_dict["bucket_key"] = bucket_key
        return await crud.update_entry(annotations, AnnotationCreation(**entry_dict), annotation_id)


@router.get("/{annotation_id}/url", response_model=AnnotationUrl, status_code=200)
async def get_annotation_url(
    annotation_id: int = Path(..., gt=0),
    requester=Security(get_current_access, scopes=[AccessType.admin, AccessType.user]),
):
    """Resolve the temporary media image URL"""
    await check_access_read(requester.id)

    # Check in DB
    annotation_instance = await check_annotation_registration(annotation_id)
    # Check in bucket
    temp_public_url = await annotations_bucket.get_public_url(annotation_instance["bucket_key"])
    return AnnotationUrl(url=temp_public_url)
