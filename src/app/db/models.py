# Copyright (C) 2022-2023, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

import enum

from sqlalchemy import ARRAY, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .session import Base


class AccessType(str, enum.Enum):
    user: str = "user"
    admin: str = "admin"


class Accesses(Base):
    __tablename__ = "accesses"

    id = Column(Integer, primary_key=True)
    login = Column(String(50), unique=True, index=True)  # index for fast lookup
    hashed_password = Column(String(70), nullable=False)
    scope = Column(Enum(AccessType), default=AccessType.user, nullable=False)

    def __repr__(self):
        return f"<Access(login='{self.login}', scope='{self.scope}')>"


class MediaType(str, enum.Enum):
    image: str = "image"
    video: str = "video"


class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True)
    bucket_key = Column(String(100), nullable=True)
    type = Column(Enum(MediaType), default=MediaType.image)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<Media(bucket_key='{self.bucket_key}', type='{self.type}'>"


class ObservationType(str, enum.Enum):
    clouds: str = "clouds"
    fire: str = "fire"
    fog: str = "fog"
    sky: str = "sky"
    smoke: str = "smoke"


class Annotations(Base):
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True)
    media_id = Column(Integer, ForeignKey("media.id"))
    observations = Column(ARRAY(Enum(ObservationType)), nullable=False)
    created_at = Column(DateTime, default=func.now())

    media = relationship("Media", uselist=False, back_populates="annotations")

    def __repr__(self):
        return f"<Media(media_id='{self.media_id}', observations='{self.observations}'>"
