# Copyright (C) 2022, Pyronear.

# This program is licensed under the Apache License version 2.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0.txt> for full license details.

import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .session import Base


class AccessType(str, enum.Enum):
    user: str = 'user'
    admin: str = 'admin'


class Accesses(Base):  # type: ignore[valid-type,misc]
    __tablename__ = "accesses"

    id = Column(Integer, primary_key=True)
    login = Column(String(50), unique=True, index=True)  # index for fast lookup
    hashed_password = Column(String(70), nullable=False)
    scope = Column(Enum(AccessType), default=AccessType.user, nullable=False)

    def __repr__(self):
        return f"<Access(login='{self.login}', scope='{self.scope}')>"


class MediaType(str, enum.Enum):
    image: str = 'image'
    video: str = 'video'


class Media(Base):  # type: ignore[valid-type,misc]
    __tablename__ = "media"

    id = Column(Integer, primary_key=True)
    bucket_key = Column(String(100), nullable=True)
    type = Column(Enum(MediaType), default=MediaType.image)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<Media(bucket_key='{self.bucket_key}', type='{self.type}'>"


class Annotations(Base):  # type: ignore[valid-type,misc]
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True)
    media_id = Column(Integer, ForeignKey("media.id"))
    bucket_key = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=func.now())

    media = relationship("Media", uselist=False, back_populates="annotations")  # type: ignore[var-annotated]

    def __repr__(self):
        return f"<Media(media_id='{self.media_id}', bucket_key='{self.bucket_key}'>"
