# Copyright (C) 2022, Pyronear contributors.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

import pytest
from fastapi import HTTPException
from fastapi.security import SecurityScopes

from app import db
from app.api import crud, deps, security
from app.api.schemas import AccessRead
from tests.db_utils import fill_table

ACCESS_TABLE = [
    {"id": 1, "login": "first_user", "hashed_password": "first_pwd_hashed", "scope": "user"},
    {"id": 2, "login": "connected_user", "hashed_password": "first_pwd_hashed", "scope": "user"},
    {"id": 3, "login": "first_device", "hashed_password": "first_pwd_hashed", "scope": "admin"},
    {"id": 4, "login": "second_device", "hashed_password": "second_pwd_hashed", "scope": "admin"},
]


@pytest.fixture(scope="function")
async def init_test_db(monkeypatch, test_db):
    monkeypatch.setattr(crud.base, "database", test_db)
    await fill_table(test_db, db.accesses, ACCESS_TABLE)


@pytest.mark.parametrize(
    "token_data, scope, expected_access, exception",
    [
        [ACCESS_TABLE[0], "user", 0, False],
        ["my_false_token", "admin", None, True],  # Decoding failure
        [{"id": 100, "scope": "admin"}, "admin", None, True],  # Unable to find access in table
        [ACCESS_TABLE[3], "admin", 3, False],  # Correct
    ],
)
@pytest.mark.asyncio
async def test_get_current_access(init_test_db, token_data, scope, expected_access, exception):

    # Create a token for the access we'll want to retrieve
    if isinstance(token_data, str):
        token = token_data
    else:
        _data = {"sub": str(token_data["id"]), "scopes": token_data["scope"].split()}
        token = await security.create_access_token(_data)
    # Check that we retrieve the correct access
    if exception:
        with pytest.raises(HTTPException):
            access = await deps.get_current_access(SecurityScopes([scope]), token=token)
    else:
        access = await deps.get_current_access(SecurityScopes([scope]), token=token)
        if isinstance(expected_access, int):
            assert access.dict() == AccessRead(**ACCESS_TABLE[expected_access]).dict()
