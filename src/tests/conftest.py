import asyncio
import io
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
import requests
from botocore.exceptions import ClientError
from httpx import AsyncClient
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.db import engine
from app.main import app
from app.models import Detection, Sequence
from app.services.storage import s3_service

dt_format = "%Y-%m-%dT%H:%M:%S.%f"
now = datetime.utcnow()

DET_TABLE = [
    {
        "id": 1,
        "created_at": now - timedelta(days=2),
        "sequence_id": 1,
        "alert_api_id": 1,
        "recorded_at": now - timedelta(days=4),
        "bucket_key": "seq1_img1.jpg",
        "algo_predictions": {
            "predictions": [{"xyxyn": [0.12, 0.13, 0.45, 0.48], "confidence": 0.87, "class_name": "smoke"}]
        },
    },
    {
        "id": 2,
        "created_at": now - timedelta(days=1),
        "sequence_id": 1,
        "alert_api_id": 1,
        "recorded_at": now - timedelta(days=3),
        "bucket_key": "seq1_img2.jpg",
        "algo_predictions": {
            "predictions": [{"xyxyn": [0.2, 0.25, 0.5, 0.55], "confidence": 0.91, "class_name": "fire"}]
        },
    },
    {
        "id": 3,
        "created_at": now,
        "sequence_id": 2,
        "alert_api_id": 1,
        "recorded_at": now - timedelta(days=2),
        "bucket_key": "seq2_img1.jpg",
        "algo_predictions": {
            "predictions": [
                {"xyxyn": [0.05, 0.05, 0.3, 0.35], "confidence": 0.76, "class_name": "smoke"},
                {"xyxyn": [0.6, 0.65, 0.85, 0.9], "confidence": 0.80, "class_name": "fire"},
            ]
        },
    },
]

SEQ_TABLE = [
    {
        "id": 1,
        "source_api": "pyronear_french",
        "alert_api_id": 1,
        # "recorded_at": now - timedelta(days=1),
        "last_seen_at": now,
        "camera_name": "habile",
        "camera_id": 1,
        "is_wildfire_alertapi": True,
        "organisation_name": "habile",
        "lat": 0.0,
        "lon": 0.0,
        "organisation_id": 1,
    }
]


@pytest.fixture(scope="session")
def event_loop(request) -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        app=app, base_url=f"http://api.localhost:8050{settings.API_V1_STR}", follow_redirects=True, timeout=5
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def async_session() -> AsyncSession:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        async with session.begin():
            for table in reversed(SQLModel.metadata.sorted_tables):
                await session.exec(table.delete())
                if hasattr(table.c, "id"):
                    await session.exec(text(f"ALTER SEQUENCE {table.name}_id_seq RESTART WITH 1"))

        yield session
        await session.rollback()


@pytest.fixture(scope="session")
def mock_img():
    # Get Pyronear logo
    return requests.get("https://avatars.githubusercontent.com/u/61667887?s=200&v=4", timeout=5).content


@pytest_asyncio.fixture(scope="function")
async def detection_session(async_session: AsyncSession):
    for entry in DET_TABLE:
        async_session.add(Detection(**entry))
    await async_session.commit()
    # Update the detection index count
    await async_session.exec(
        text(
            f"ALTER SEQUENCE {Detection.__tablename__}_id_seq RESTART WITH {max(entry['id'] for entry in DET_TABLE) + 1}"
        )
    )
    await async_session.commit()
    # Create bucket files
    for entry in DET_TABLE:
        bucket = s3_service.get_bucket(s3_service.resolve_bucket_name())
        bucket.upload_file(entry["bucket_key"], io.BytesIO(b""))
    yield async_session
    await async_session.rollback()
    # Delete bucket files
    try:
        for entry in DET_TABLE:
            bucket = s3_service.get_bucket(s3_service.resolve_bucket_name())
            bucket.delete_file(entry["bucket_key"])
    except ClientError:
        pass


@pytest_asyncio.fixture(scope="function")
async def sequence_session(async_session: AsyncSession):
    for entry in SEQ_TABLE:
        async_session.add(Sequence(**entry))
    await async_session.commit()
    # Update the detection index count
    await async_session.exec(
        text(
            f"ALTER SEQUENCE {Sequence.__tablename__}_id_seq RESTART WITH {max(entry['id'] for entry in SEQ_TABLE) + 1}"
        )
    )
    await async_session.commit()

    yield async_session
    await async_session.rollback()


def pytest_configure():
    # Table
    pytest.detection_table = [
        {k: datetime.strftime(v, dt_format) if isinstance(v, datetime) else v for k, v in entry.items()}
        for entry in DET_TABLE
    ]
    pytest.sequence_table = [
        {k: datetime.strftime(v, dt_format) if isinstance(v, datetime) else v for k, v in entry.items()}
        for entry in SEQ_TABLE
    ]
