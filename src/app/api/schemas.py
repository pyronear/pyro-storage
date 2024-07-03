# Copyright (C) 2022-2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from app.db.models import AccessType, MediaType


# Template classes
class _CreatedAt(BaseModel):
    created_at: Optional[datetime] = None

    @validator("created_at", pre=True, always=True)
    def default_ts_created(v):
        return v or datetime.utcnow()


class _Id(BaseModel):
    id: int = Field(..., gt=0)


# Accesses
class Login(BaseModel):
    login: str = Field(..., min_length=3, max_length=50, example="JohnDoe")


class Cred(BaseModel):
    password: str = Field(..., min_length=3, example="PickARobustOne")


class CredHash(BaseModel):
    hashed_password: str


class AccessBase(Login):
    scope: AccessType = AccessType.user


class AccessAuth(AccessBase, Cred):
    pass


class AccessCreation(AccessBase, CredHash):
    pass


class AccessRead(AccessBase, _Id):
    pass


# Token
class Token(BaseModel):
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.423fgFGTfttrvU6D1k7vF92hH5vaJHCGFYd8E")
    token_type: str = Field(..., example="bearer")


class TokenPayload(BaseModel):
    user_id: Optional[str] = None  # token sub
    scopes: List[AccessType] = []


# Media
class BaseMedia(BaseModel):
    type: MediaType = MediaType.image


class MediaIn(BaseMedia):
    pass


class MediaCreation(MediaIn):
    bucket_key: str = Field(...)


class MediaOut(MediaIn, _CreatedAt, _Id):
    pass


class MediaUrl(BaseModel):
    url: str


# Annotation
class AnnotationIn(BaseModel):
    media_id: int = Field(..., gt=0)


class AnnotationCreation(AnnotationIn):
    bucket_key: str = Field(...)


class AnnotationOut(AnnotationIn, _CreatedAt, _Id):
    pass


class AnnotationUrl(BaseModel):
    url: str
