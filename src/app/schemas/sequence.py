# Copyright (C) 2020-2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.


from typing import Dict, Optional

from pydantic import BaseModel, Field

__all__ = ["Azimuth", "SequenceCreate", "SequenceUpdateBboxAuto", "SequenceUpdateBboxVerified"]


class Azimuth(BaseModel):
    azimuth: float = Field(
        ...,
        gt=0,
        lt=360,
        description="angle between north and direction in degrees",
        json_schema_extra={"examples": [110]},
    )


class SequenceCreate(Azimuth):
    source_api: str = Field(nullable=False)
    alert_api_id: int = Field(nullable=False)
    camera_name: str = Field(nullable=False)
    azimuth: Optional[int] = Field(default=None)
    is_wildfire_alertapi: bool = Field(nullable=False)
    organisation: str = Field(nullable=False)
    algo_prediction: Optional[Dict] = Field(default=None, sa_column_kwargs={"type_": "jsonb"})


class SequenceUpdateBboxAuto(BaseModel):
    algo_prediction: Optional[Dict] = Field(default=None, sa_column_kwargs={"type_": "jsonb"})


class SequenceUpdateBboxVerified(BaseModel):
    algo_prediction: Optional[Dict] = Field(default=None, sa_column_kwargs={"type_": "jsonb"})
