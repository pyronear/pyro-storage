# Copyright (C) 2021, Pyronear contributors.

# This program is licensed under the Apache License version 2.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0.txt> for full license details.

import pytest
from fastapi import HTTPException

from app import db
from app.api import crud
from tests.db_utils import fill_table
from tests.utils import update_only_datetime

ACCESS_TABLE = [
    {"id": 1, "login": "first_login", "hashed_password": "hashed_pwd", "scope": "user"},
    {"id": 2, "login": "second_login", "hashed_password": "hashed_pwd", "scope": "admin"},
]

MEDIA_TABLE = [
    {"id": 1, "type": "image", "created_at": "2020-10-13T08:18:45.447773"},
    {"id": 2, "type": "video", "created_at": "2020-10-13T09:18:45.447773"},
]


ANNOTATIONS_TABLE = [
    {"id": 1, "media_id": 1, "created_at": "2020-10-13T08:18:45.447773"},
]


MEDIA_TABLE_FOR_DB = list(map(update_only_datetime, MEDIA_TABLE))
ANNOTATIONS_TABLE_FOR_DB = list(map(update_only_datetime, ANNOTATIONS_TABLE))


@pytest.fixture(scope="function")
async def init_test_db(monkeypatch, test_db):
    monkeypatch.setattr(crud.base, "database", test_db)
    await fill_table(test_db, db.accesses, ACCESS_TABLE)
    await fill_table(test_db, db.media, MEDIA_TABLE_FOR_DB)
    await fill_table(test_db, db.annotations, ANNOTATIONS_TABLE_FOR_DB)


@pytest.mark.parametrize(
    "access_id, expected_result",
    [
        [1, False],
        [2, True],
    ],
)
@pytest.mark.asyncio
async def test_admin_access(test_app_asyncio, init_test_db, access_id, expected_result):
    admin_access_result = await crud.authorizations.is_admin_access(access_id)
    assert admin_access_result == expected_result


@pytest.mark.parametrize(
    "access_id, should_raise",
    [
        [1, False],
        [2, True],  # Because Admin
    ],
)
@pytest.mark.asyncio
async def test_check_access_read(test_app_asyncio, init_test_db, access_id, should_raise):
    if should_raise:
        with pytest.raises(HTTPException):
            await crud.authorizations.check_access_read(access_id)
    else:
        await crud.authorizations.check_access_read(access_id)
