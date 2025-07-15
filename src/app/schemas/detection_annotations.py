# Copyright (C) 2020-2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.


from datetime import datetime
from typing import Dict

from pydantic import BaseModel, Field

from app.models import DetectionAnnotationProcessingStage

__all__ = ["DetectionAnnotationCreate", "DetectionAnnotationUpdate"]


class DetectionAnnotationCreate(BaseModel):
    detection_id: int = Field(foreign_key="detections.id", nullable=False)
    annotation: Dict = Field(nullable=False, sa_column_kwargs={"type_": "jsonb"})
    processing_stages: DetectionAnnotationProcessingStage = Field(nullable=False, sa_column_kwargs={"type_": "jsonb"})


class DetectionAnnotationUpdate(BaseModel):
    annotation: Dict = Field(nullable=False, sa_column_kwargs={"type_": "jsonb"})
    processing_stages: DetectionAnnotationProcessingStage = Field(nullable=False, sa_column_kwargs={"type_": "jsonb"})
    updated_at: datetime = Field(default_factory=datetime.utcnow)
