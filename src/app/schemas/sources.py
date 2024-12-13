# Copyright (C) 2020-2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

from typing import Union

from pydantic import BaseModel, Field

from app.models import Origin

__all__ = ["SourceCreate", "UpdateSource"]


class UpdateSource(BaseModel):
    camera_id: Union[int, None] = Field(default=None, gt=0)
    origin: Origin
    origin_url: Union[str, None] = Field(default=None)


class SourceCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="name of the source",
        json_schema_extra={"examples": ["pyro-source-01"]},
    )
    camera_id: Union[int, None] = Field(default=None, gt=0)
    origin: Origin
    origin_url: Union[str, None] = Field(default=None)

    angle_of_view: float = Field(
        ...,
        gt=0,
        le=360,
        description="angle between left and right source view",
        json_schema_extra={"examples": [120.0]},
    )
    elevation: float = Field(
        ...,
        gt=0,
        lt=10000,
        description="number of meters from sea level",
        json_schema_extra={"examples": [1582]},
    )
    lat: float = Field(..., gt=-90, lt=90, description="latitude", json_schema_extra={"examples": [44.765181]})
    lon: float = Field(..., gt=-180, lt=180, description="longitude", json_schema_extra={"examples": [4.514880]})
