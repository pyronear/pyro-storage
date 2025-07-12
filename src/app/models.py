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


class SequenceStage(str, Enum):
    IMPORTED = "imported"
    READY_TO_ANNOTATE = "ready_to_annotate"
    ANNOTATED = "annotated"


class Stage(str, Enum):
    VISUAL_CHECK = "visual_check"
    DATASET_READY = "dataset_ready"
    LABEL_STUDIO_CHECK = "label_studio_check"


# -------------------- TABLES --------------------


class Sequence(SQLModel, table=True):
    __tablename__ = "sequences"
    id: Optional[int] = Field(default=None, primary_key=True)
    source_api: str = Field(nullable=False)
    alert_api_id: int = Field(nullable=False)
    created_at: datetime = Field(nullable=False)
    last_seen_at: datetime = Field(nullable=False)
    camera_name: str = Field(nullable=False)
    azimuth: Optional[int] = Field(default=None)
    is_wildfire_alertapi: bool = Field(nullable=False)
    organisation: str = Field(nullable=False)
    algo_prediction: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    # {
    #   sequences_bbox: [{
    #   is_smoke: bool,
    #   false_positive_types: [lens_flare|high_cloud|lens_droplet|..., ...],
    #   bboxes: [{detection_id: int, xyxyn: [x1n y1n x2n y2n]}]
    #   }, ...]
    # }


class SequenceAnnotation(SQLModel, table=True):
    __tablename__ = "labels_sequence_annotation"
    id: Optional[int] = Field(default=None, primary_key=True)
    sequence_id: int = Field(foreign_key="sequences.id", nullable=False)
    has_smoke: bool = Field(nullable=False)
    has_false_positives: bool = Field(nullable=False)
    has_missed_smoke: bool = Field(nullable=False)
    sequence_bbox_predictions_annotation: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    # {
    #   sequences_bbox: [{
    #   is_smoke: bool,
    #   gif_url_main : str,
    #   gif_url_crop : str,
    #   false_positive_types: [lens_flare|high_cloud|lens_droplet|..., ...],
    #   bboxes: [{detection_id: int, xyxyn: [x1n y1n x2n y2n]}]
    #   }, ...]
    # }
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    sequence_stage: SequenceStage = Field(nullable=False)


class Detection(SQLModel, table=True):
    __tablename__ = "detections"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    sequence_id: Optional[int] = Field(foreign_key="sequences.id", nullable=True)
    bucket_key: str = Field(nullable=False)
    algo_prediction: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    # {predictions: [{xyxyn: [x1n y1n x2n y2n], confidence: float, class_name: 'smoke'}, ...]}


class DetectionAnnotation(SQLModel, table=True):
    __tablename__ = "labels_detection_annotation"
    id: Optional[int] = Field(default=None, primary_key=True)
    source_api: str = Field(nullable=False)
    alert_api_id: int = Field(nullable=False)
    detection_id: int = Field(foreign_key="detections.id", nullable=False)
    annotation: dict = Field(default=None, sa_column=Column(JSONB))
    # {predictions: [{xyxyn: [x1n y1n x2n y2n], confidence: float, class_name: 'smoke'}, ...]}
    processing_stages: dict = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: Optional[datetime] = Field(default=None)
