import json

import pytest
import pytest_asyncio

from app import db
from app.api import crud, security
from tests.db_utils import fill_table, get_entry
from tests.utils import update_only_datetime

ACCESS_TABLE = [
    {"id": 1, "login": "first_login", "hashed_password": "hashed_pwd", "scope": "user"},
    {"id": 2, "login": "second_login", "hashed_password": "hashed_pwd", "scope": "admin"},
]


ACCESS_TABLE_FOR_DB = list(map(update_only_datetime, ACCESS_TABLE))


@pytest_asyncio.fixture(scope="function")
async def init_test_db(monkeypatch, test_db):
    monkeypatch.setattr(crud.base, "database", test_db)
    await fill_table(test_db, db.accesses, ACCESS_TABLE)
    monkeypatch.setattr(security, "hash_password", pytest.mock_hash_password)


@pytest.mark.parametrize(
    "access_idx, access_id, status_code, status_details",
    [
        [None, 1, 401, "Not authenticated"],
        [0, 1, 403, "Your access scope is not compatible with this operation."],
        [0, 2, 403, "Your access scope is not compatible with this operation."],
        [0, 3, 403, "Your access scope is not compatible with this operation."],
        [1, 1, 200, None],
        [1, 2, 200, None],
        [1, 999, 404, "Table accesses has no entry with id=999"],
        [1, 0, 422, None],
    ],
)
@pytest.mark.asyncio
async def test_get_access(init_test_db, test_app_asyncio, access_idx, access_id, status_code, status_details):

    # Create a custom access token
    auth = None
    if isinstance(access_idx, int):
        auth = await pytest.get_token(ACCESS_TABLE[access_idx]["id"], ACCESS_TABLE[access_idx]["scope"].split())

    response = await test_app_asyncio.get(f"/accesses/{access_id}", headers=auth)
    assert response.status_code == status_code

    if isinstance(status_details, str):
        assert response.json()["detail"] == status_details

    if response.status_code == 200:
        access = None
        for _access in ACCESS_TABLE:
            if _access["id"] == access_id:
                access = _access
                break
        assert response.json() == {k: v for k, v in access.items() if k != "hashed_password"}


@pytest.mark.parametrize(
    "access_idx, status_code, status_details",
    [
        [None, 401, "Not authenticated"],
        [0, 403, "Your access scope is not compatible with this operation."],
        [1, 200, None],
    ],
)
@pytest.mark.asyncio
async def test_fetch_accesses(init_test_db, test_app_asyncio, access_idx, status_code, status_details):

    # Create a custom access token
    auth = None
    if isinstance(access_idx, int):
        auth = await pytest.get_token(ACCESS_TABLE[access_idx]["id"], ACCESS_TABLE[access_idx]["scope"].split())

    response = await test_app_asyncio.get("/accesses/", headers=auth)
    assert response.status_code == status_code

    if isinstance(status_details, str):
        assert response.json()["detail"] == status_details
    if response.status_code == 200:
        assert response.json() == [{k: v for k, v in entry.items() if k != "hashed_password"} for entry in ACCESS_TABLE]


@pytest.mark.parametrize(
    "access_idx, payload, status_code, status_details",
    [
        [None, {"login": "dummy_login", "scope": "admin", "password": "my_pwd"}, 401, "Not authenticated"],
        # non-admin can't create access
        [
            0,
            {"login": "dummy_login", "scope": "user", "password": "my_pwd"},
            403,
            "Your access scope is not compatible with this operation.",
        ],
        [
            0,
            {"login": "dummy_login", "scope": "admin", "password": "my_pwd"},
            403,
            "Your access scope is not compatible with this operation.",
        ],
        [1, {"login": "dummy_login", "scope": "user", "password": "my_pwd"}, 201, None],
        [1, {"login": "dummy_login", "scope": "admin", "password": "my_pwd"}, 201, None],
        [1, {"login": 1, "scope": "admin", "password": "my_pwd"}, 422, None],
        [1, {"login": "dummy_login", "scope": 1, "password": "my_pwd"}, 422, None],
    ],
)
@pytest.mark.asyncio
async def test_create_access(test_app_asyncio, init_test_db, test_db, access_idx, payload, status_code, status_details):

    # Create a custom access token
    auth = None
    if isinstance(access_idx, int):
        auth = await pytest.get_token(ACCESS_TABLE[access_idx]["id"], ACCESS_TABLE[access_idx]["scope"].split())

    response = await test_app_asyncio.post("/accesses/", data=json.dumps(payload), headers=auth)
    assert response.status_code == status_code
    if isinstance(status_details, str):
        assert response.json()["detail"] == status_details

    if response.status_code // 100 == 2:
        json_response = response.json()
        test_response = {"id": len(ACCESS_TABLE) + 1, "login": payload["login"], "scope": payload["scope"]}
        assert json_response == test_response

        new_annotation = await get_entry(test_db, db.accesses, json_response["id"])
        new_annotation = dict(**new_annotation)


@pytest.mark.parametrize(
    "access_idx, payload, access_id, status_code, status_details",
    [
        [None, {}, 1, 401, "Not authenticated"],
        [0, {"password": "my_pwd"}, 1, 403, "Your access scope is not compatible with this operation."],
        [1, {"password": "my_pwd"}, 1, 200, None],
        [1, {}, 1, 422, None],
        [1, {"password": 1}, 1, 422, None],
        [1, {"password": "my_pwd"}, 999, 404, "Table accesses has no entry with id=999"],
        [1, {"password": "my_pwd"}, 2, 200, None],
    ],
)
@pytest.mark.asyncio
async def test_update_access_pwd(
    test_app_asyncio, init_test_db, test_db, access_idx, payload, access_id, status_code, status_details
):

    # Create a custom access token
    auth = None
    if isinstance(access_idx, int):
        auth = await pytest.get_token(ACCESS_TABLE[access_idx]["id"], ACCESS_TABLE[access_idx]["scope"].split())

    response = await test_app_asyncio.put(f"/accesses/{access_id}/", data=json.dumps(payload), headers=auth)
    assert response.status_code == status_code
    if isinstance(status_details, str):
        assert response.json()["detail"] == status_details

    if response.status_code // 100 == 2:
        updated_access = await get_entry(test_db, db.accesses, access_id)
        updated_access = dict(**updated_access)
        for k, v in updated_access.items():
            if k == "hashed_password":
                assert v == f"hashed_{payload['password']}"
            else:
                assert v == payload.get(k, ACCESS_TABLE_FOR_DB[access_id - 1][k])


@pytest.mark.parametrize(
    "access_idx, access_id, status_code, status_details",
    [
        [None, 1, 401, "Not authenticated"],
        [0, 1, 403, "Your access scope is not compatible with this operation."],
        [1, 1, 200, None],
        [1, 999, 404, "Table accesses has no entry with id=999"],
        [1, 0, 422, None],
    ],
)
@pytest.mark.asyncio
async def test_delete_access(test_app_asyncio, init_test_db, access_idx, access_id, status_code, status_details):

    # Create a custom access token
    auth = None
    if isinstance(access_idx, int):
        auth = await pytest.get_token(ACCESS_TABLE[access_idx]["id"], ACCESS_TABLE[access_idx]["scope"].split())

    response = await test_app_asyncio.delete(f"/accesses/{access_id}/", headers=auth)
    assert response.status_code == status_code
    if isinstance(status_details, str):
        assert response.json()["detail"] == status_details

    if response.status_code // 100 == 2:
        assert response.json() == {k: v for k, v in ACCESS_TABLE[access_id - 1].items() if k != "hashed_password"}
        remaining_annotation = await test_app_asyncio.get("/accesses/", headers=auth)
        assert all(entry["id"] != access_id for entry in remaining_annotation.json())
