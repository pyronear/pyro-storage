# Copyright (C) 2020-2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.


from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field

from app.models import SequenceAnnotationProcessingStage

__all__ = ["SequenceAnnotationCreate", "SequenceAnnotationUpdate"]


class SequenceAnnotationCreate(BaseModel):
    sequence_id: int = Field(foreign_key="sequences.id", nullable=False)
    has_smoke: bool = Field(nullable=False)
    has_false_positives: bool = Field(nullable=False)
    false_positive_types: str = Field(nullable=False)
    has_missed_smoke: bool = Field(nullable=False)
    annotation: Optional[Dict] = Field(default=None, sa_column_kwargs={"type_": "jsonb"})
    processing_stage: SequenceAnnotationProcessingStage = Field(nullable=False)


class SequenceAnnotationUpdate(BaseModel):
    has_smoke: bool = Field(nullable=False)
    has_false_positives: bool = Field(nullable=False)
    false_positive_types: str = Field(nullable=False)
    has_missed_smoke: bool = Field(nullable=False)
    annotation: Optional[Dict] = Field(default=None, sa_column_kwargs={"type_": "jsonb"})
    processing_stage: SequenceAnnotationProcessingStage = Field(nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
