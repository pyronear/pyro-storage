# Copyright (C) 2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from datetime import datetime
from typing import List, Optional, cast

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Path,
    Query,
    Security,
    UploadFile,
    status,
)
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import (
    get_detection_crud,
    get_jwt,
    get_source_crud,
)
from app.core.config import settings
from app.crud import DetectionCRUD, SourceCRUD
from app.db import get_session
from app.models import Detection, Role, Source, UserRole
from app.schemas.detections import (
    BOXES_PATTERN,
    COMPILED_BOXES_PATTERN,
    DetectionCreate,
    DetectionLabel,
    DetectionUrl,
    DetectionWithUrl,
)
from app.schemas.login import TokenPayload
from app.services.storage import s3_service, upload_file

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Register a new wildfire detection")
async def create_detection(
    bboxes: str = Form(
        ...,
        description="string representation of list of detection localizations, each represented as a tuple of relative coords (max 3 decimals) in order: xmin, ymin, xmax, ymax, conf",
        pattern=BOXES_PATTERN,
        min_length=2,
        max_length=settings.MAX_BBOX_STR_LENGTH,
    ),
    azimuth: float = Form(..., gt=0, lt=360, description="angle between north and direction in degrees"),
    file: UploadFile = File(..., alias="file"),
    detections: DetectionCRUD = Depends(get_detection_crud),
    token_payload: TokenPayload = Security(get_jwt, scopes=[Role.CAMERA]),
) -> Detection:
    # Throw an error if the format is invalid and can't be captured by the regex
    if any(box[0] >= box[2] or box[1] >= box[3] for box in COMPILED_BOXES_PATTERN.findall(bboxes)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="xmin & ymin are expected to be respectively smaller than xmax & ymax",
        )

    # Upload media
    bucket_key = await upload_file(file, token_payload._id, token_payload.sub)
    await detections.create(
        DetectionCreate(source_id=token_payload.sub, bucket_key=bucket_key, azimuth=azimuth, bboxes=bboxes)
    )


@router.get("/{detection_id}", status_code=status.HTTP_200_OK, summary="Fetch the information of a specific detection")
async def get_detection(
    detection_id: int = Path(..., gt=0),
    sources: SourceCRUD = Depends(get_source_crud),
    detections: DetectionCRUD = Depends(get_detection_crud),
    token_payload: TokenPayload = Security(get_jwt, scopes=[UserRole.ADMIN, UserRole.AGENT, UserRole.USER]),
) -> Detection:
    detection = cast(Detection, await detections.get(detection_id, strict=True))

    if UserRole.ADMIN in token_payload.scopes:
        return detection

    camera = cast(Source, await sources.get(detection.source_id, strict=True))
    if token_payload._id != camera._id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden.")
    return detection


@router.get("/{detection_id}/url", response_model=DetectionUrl, status_code=200)
async def get_detection_url(
    detection_id: int = Path(..., gt=0),
    sources: SourceCRUD = Depends(get_source_crud),
    detections: DetectionCRUD = Depends(get_detection_crud),
    token_payload: TokenPayload = Security(get_jwt, scopes=[UserRole.ADMIN, UserRole.AGENT, UserRole.USER]),
) -> DetectionUrl:
    """Resolve the temporary media image URL"""
    # Check in DB
    detection = cast(Detection, await detections.get(detection_id, strict=True))

    if UserRole.ADMIN in token_payload.scopes:
        camera = cast(Source, await sources.get(detection.source_id, strict=True))
        bucket = s3_service.get_bucket(s3_service.resolve_bucket_name(camera._id))
        return DetectionUrl(url=bucket.get_public_url(detection.bucket_key))

    camera = cast(Source, await sources.get(detection.source_id, strict=True))
    if token_payload._id != camera._id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden.")
    # Check in bucket
    bucket = s3_service.get_bucket(s3_service.resolve_bucket_name(camera._id))
    return DetectionUrl(url=bucket.get_public_url(detection.bucket_key))


@router.get("/", status_code=status.HTTP_200_OK, summary="Fetch all the detections")
async def fetch_detections(
    detections: DetectionCRUD = Depends(get_detection_crud),
    sources: SourceCRUD = Depends(get_source_crud),
    token_payload: TokenPayload = Security(get_jwt, scopes=[UserRole.ADMIN, UserRole.AGENT, UserRole.USER]),
) -> List[Detection]:
    if UserRole.ADMIN in token_payload.scopes:
        return [elt for elt in await detections.fetch_all()]

    sources_list = await sources.fetch_all(filter_pair=("_id", token_payload._id))
    source_ids = [camera.id for camera in sources_list]

    return await detections.fetch_all(in_pair=("source_id", source_ids))


@router.get("/unlabeled/fromdate", status_code=status.HTTP_200_OK, summary="Fetch all the unlabeled detections")
async def fetch_unlabeled_detections(
    from_date: datetime = Query(),
    limit: Optional[int] = Query(15, description="Maximum number of detections to fetch"),
    offset: Optional[int] = Query(0, description="Number of detections to skip before starting to fetch"),
    session: AsyncSession = Depends(get_session),
    token_payload: TokenPayload = Security(get_jwt, scopes=[UserRole.ADMIN, UserRole.AGENT, UserRole.USER]),
) -> List[DetectionWithUrl]:
    if UserRole.ADMIN in token_payload.scopes:
        # Custom SQL query to fetch detections along with corresponding _id
        query = await session.exec(
            select(Detection, Source.id)  # type: ignore[attr-defined]
            .join(Source, Detection.source_id == Source.id)  # type: ignore[arg-type]
            .where(Detection.is_wildfire.is_(None))  # type: ignore[union-attr]
            .where(Detection.created_at >= from_date)
            .limit(limit)
            .offset(offset)
        )
        results = query.all()
        unlabeled_detections = [Detection(**detection.__dict__) for detection, _ in results]
        urls = [
            s3_service.get_bucket(s3_service.resolve_bucket_name(org_id)).get_public_url(det.bucket_key)
            for det, org_id in results
        ]
    else:
        query = await session.exec(
            select(Detection)  # type: ignore[attr-defined]
            .join(Source, Detection.source_id == Source.id)  # type: ignore[arg-type]
            .where(Detection.is_wildfire.is_(None))  # type: ignore[union-attr]
            .where(Detection.created_at >= from_date)
            .where(Source.id == token_payload._id)
            .limit(limit)
            .offset(offset)
        )
        results = query.all()
        unlabeled_detections = [Detection(**detection.__dict__) for detection in results]
        bucket = s3_service.get_bucket(s3_service.resolve_bucket_name(token_payload._id))
        urls = [bucket.get_public_url(detection.bucket_key) for detection in unlabeled_detections]

    return [DetectionWithUrl(**detection.model_dump(), url=url) for detection, url in zip(unlabeled_detections, urls)]


@router.patch("/{detection_id}/label", status_code=status.HTTP_200_OK, summary="Label the nature of the detection")
async def label_detection(
    payload: DetectionLabel,
    detection_id: int = Path(..., gt=0),
    sources: SourceCRUD = Depends(get_source_crud),
    detections: DetectionCRUD = Depends(get_detection_crud),
    token_payload: TokenPayload = Security(get_jwt, scopes=[UserRole.ADMIN, UserRole.AGENT]),
) -> Detection:
    detection = cast(Detection, await detections.get(detection_id, strict=True))

    if UserRole.ADMIN in token_payload.scopes:
        return await detections.update(detection_id, payload)

    camera = cast(Source, await sources.get(detection.source_id, strict=True))
    if token_payload._id != camera._id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden.")
    return await detections.update(detection_id, payload)


@router.delete("/{detection_id}", status_code=status.HTTP_200_OK, summary="Delete a detection")
async def delete_detection(
    detection_id: int = Path(..., gt=0),
    detections: DetectionCRUD = Depends(get_detection_crud),
    sources: SourceCRUD = Depends(get_source_crud),
    token_payload: TokenPayload = Security(get_jwt, scopes=[UserRole.ADMIN]),
) -> None:
    detection = cast(Detection, await detections.get(detection_id, strict=True))
    camera = cast(Source, await sources.get(detection.source_id, strict=True))
    bucket = s3_service.get_bucket(s3_service.resolve_bucket_name(camera._id))
    bucket.delete_file(detection.bucket_key)
    await detections.delete(detection_id)
