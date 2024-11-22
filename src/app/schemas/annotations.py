# Copyright (C) 2020-2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.


from pydantic import BaseModel, Field

from app.models import Label

__all__ = ["AnnotationCreate"]


class AnnotationCreate(BaseModel):
    id: int = Field(..., gt=0)
    gif_url: str
    label: Label

class AnnotationIn(BaseModel):
    label: Label

class AnnotationOut(AnnotationIn):
    pass

class AnnotationUrl(BaseModel):
    gif_url: str
