# Copyright (C) 2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column

# from sqlalchemy.sql.sqltypes import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

__all__ = ["Detection", "DetectionAnnotation", "Sequence", "SequenceAnnotation"]

# -------------------- ENUMS --------------------


class DetectionAnnotationProcessingStage(str, Enum):
    IMPORTED = "imported"
    VISUAL_CHECK = "visual_check"
    LABEL_STUDIO_CHECK = "label_studio_check"
    ANNOTATED = "annotated"


class SequenceAnnotationProcessingStage(str, Enum):
    IMPORTED = "imported"
    READY_TO_ANNOTATE = "ready_to_annotate"
    ANNOTATED = "annotated"


class SourceApi(str, Enum):
    PYRONEAR_FRENCH_API = "pyronear_french"
    ALERT_WILDFIRE = "alert_wildfire"
    CENIA = "api_cenia"


# -------------------- TABLES --------------------


class Sequence(SQLModel, table=True):
    __tablename__ = "sequences"
    id: int = Field(default=None, primary_key=True)
    source_api: SourceApi = Field(nullable=False)
    alert_api_id: int = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    # recorded_at: datetime = Field(nullable=False)
    last_seen_at: datetime = Field(nullable=False)
    camera_name: str = Field(nullable=False)
    camera_id: int = Field(nullable=False)
    lat: float = Field(nullable=False)
    lon: float = Field(nullable=False)
    azimuth: Optional[int] = Field(default=None)
    is_wildfire_alertapi: bool = Field(nullable=False)
    organisation_name: str = Field(nullable=False)
    organisation_id: int = Field(nullable=False)

    # algo_prediction: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    # {
    #   sequences_bbox: [{
    #   is_smoke: bool,
    #   false_positive_types: [lens_flare|high_cloud|lens_droplet|..., ...],
    #   bboxes: [{detection_id: int, xyxyn: [x1n y1n x2n y2n]}]
    #   }, ...]
    # }


class SequenceAnnotation(SQLModel, table=True):
    __tablename__ = "labels_sequence_annotation"
    id: int = Field(default=None, primary_key=True)
    sequence_id: int = Field(foreign_key="sequences.id", nullable=False)
    has_smoke: bool = Field(nullable=False)
    has_false_positives: bool = Field(nullable=False)
    false_positive_types: str = Field(nullable=False)
    has_missed_smoke: bool = Field(nullable=False)
    #annotation: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    # {
    #   sequences_bbox: [{
    #   is_smoke: bool,
    #   gif_url_main : str,
    #   gif_url_crop : str,
    #   false_positive_types: [lens_flare|high_cloud|lens_droplet|..., ...],
    #   bboxes: [{detection_id: int, xyxyn: [x1n y1n x2n y2n]}]
    #   }, ...]
    # }
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: Optional[datetime] = Field(default=None)
    processing_stage: SequenceAnnotationProcessingStage = Field(nullable=False)


class Detection(SQLModel, table=True):
    __tablename__ = "detections"
    id: int = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    recorded_at: datetime = Field(nullable=False)
    alert_api_id: int = Field(nullable=False)
    sequence_id: Optional[int] = Field(foreign_key="sequences.id", nullable=True)
    bucket_key: str = Field(nullable=False)
    algo_predictions: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    # {predictions: [{xyxyn: [x1n y1n x2n y2n], confidence: float, class_name: 'smoke'}, ...]}


class DetectionAnnotation(SQLModel, table=True):
    __tablename__ = "labels_detection_annotation"
    id: int = Field(default=None, primary_key=True)
    detection_id: int = Field(foreign_key="detections.id", nullable=False)
    annotation: dict = Field(default=None, sa_column=Column(JSONB))
    # {predictions: [{xyxyn: [x1n y1n x2n y2n], confidence: float, class_name: 'smoke'}, ...]}
    processing_stages: DetectionAnnotationProcessingStage = Field(default=None, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: Optional[datetime] = Field(default=None)
