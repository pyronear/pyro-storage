# Copyright (C) 2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from datetime import datetime
from enum import Enum
from typing import Union

from sqlmodel import Field, SQLModel

from app.core.config import settings

__all__ = ["Annotation", "Detection", "Source", "User"]


class UserRole(str, Enum):
    ADMIN: str = "admin"
    AGENT: str = "agent"
    USER: str = "user"


class Role(str, Enum):
    ADMIN: str = "admin"
    AGENT: str = "agent"
    SOURCE: str = "source"
    USER: str = "user"


class Label(str, Enum):
    WILDFIRE: str = "wildfire"
    NOTHING: str = "nothing"
    UNSURE: str = "unsure"


class Origin(str, Enum):
    PYRONEARFRENCHAPI: str = "pyronearfrenchapi"
    ALERTWILDFIRE: str = "alertwildfire"


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int = Field(None, primary_key=True)
    source_id: int = Field(..., foreign_key="sources.id", nullable=False)
    role: UserRole = Field(UserRole.USER, nullable=False)
    # Allow sign-up/in via login + password
    login: str = Field(..., index=True, unique=True, min_length=2, max_length=50, nullable=False)
    hashed_password: str = Field(..., min_length=5, max_length=70, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Source(SQLModel, table=True):
    __tablename__ = "sources"
    id: int = Field(None, primary_key=True)
    name: str = Field(..., min_length=5, max_length=100, nullable=False, unique=True)
    camera_id: int = Field(default=None, nullable=True)
    origin: Origin = Field(default=None, nullable=True)
    origin_url: str = Field(default=None, nullable=True)
    angle_of_view: float = Field(..., gt=0, le=360, nullable=True)
    elevation: float = Field(..., gt=0, lt=10000, nullable=True)
    lat: float = Field(..., gt=-90, lt=90, nullable=True)
    lon: float = Field(..., gt=-180, lt=180, nullable=True)
    is_trustable: bool = True
    last_active_at: Union[datetime, None] = None
    last_image: Union[str, None] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Detection(SQLModel, table=True):
    __tablename__ = "detections"
    id: int = Field(None, primary_key=True)
    source_id: int = Field(..., foreign_key="sources.id", nullable=False)
    annotation_id: int = Field(None, foreign_key="annotations.id", nullable=True)
    azimuth: float = Field(..., gt=0, lt=360)
    bucket_key: str
    bboxes: str = Field(..., min_length=2, max_length=settings.MAX_BBOX_STR_LENGTH, nullable=False)
    bbox_verified: str = Field(None, min_length=2, max_length=settings.MAX_BBOX_STR_LENGTH, nullable=True)
    prediction: float = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Annotation(SQLModel, table=True):
    __tablename__ = "annotations"
    id: int = Field(None, primary_key=True)
    gif_url: str = Field(nullable=False)
    label: Label = Field(nullable=True)
