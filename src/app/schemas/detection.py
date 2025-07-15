# Copyright (C) 2020-2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.


from typing import Dict, Optional

from pydantic import BaseModel, Field

__all__ = [
    "DetectionCreate",
    "DetectionUrl",
    "DetectionWithUrl",
]


class DetectionCreate(BaseModel):
    sequence_id: Optional[int]
    bucket_key: str
    algo_predictions: Dict


class DetectionUrl(BaseModel):
    img_url: str = Field(..., description="temporary URL to access the media content")


class DetectionWithUrl(DetectionCreate):
    img_url: str = Field(..., description="temporary URL to access the media content")
