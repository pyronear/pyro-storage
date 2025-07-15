# Copyright (C) 2020-2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.


from typing import Dict

from pydantic import BaseModel, Field

__all__ = ["DetectionAnnotation", "DetectionAnnotationCreate"]


class DetectionAnnotationCreate(BaseModel):
    source_api: str = Field(nullable=False)
    alert_api_id: int = Field(nullable=False)
    detection_id: int = Field(foreign_key="detections.id", nullable=False)
    annotation: Dict = Field(nullable=False, sa_column_kwargs={"type_": "jsonb"})
    processing_stages: Dict = Field(nullable=False, sa_column_kwargs={"type_": "jsonb"})


class DetectionAnnotation(BaseModel):
    annotation: Dict = Field(nullable=False, sa_column_kwargs={"type_": "jsonb"})
