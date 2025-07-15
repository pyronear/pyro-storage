# Copyright (C) 2020-2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.


from typing import Dict, Optional

from pydantic import BaseModel, Field

from app.models import SequenceStage

__all__ = ["SequenceAnnotation"]


class SequenceAnnotation(BaseModel):
    sequence_id: int = Field(foreign_key="sequences.id", nullable=False)
    has_smoke: bool = Field(nullable=False)
    has_false_positives: bool = Field(nullable=False)
    has_missed_smoke: bool = Field(nullable=False)
    sequence_bbox_predictions_annotation: Optional[Dict] = Field(default=None, sa_column_kwargs={"type_": "jsonb"})
    sequence_stage: SequenceStage = Field(nullable=False)
