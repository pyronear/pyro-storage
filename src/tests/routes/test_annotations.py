# Copyright (C) 2022, Pyronear contributors.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

import json
import os
import tempfile
from datetime import datetime

import pytest

from app import db
from app.api import crud
from app.services import annotations_bucket
from tests.db_utils import TestSessionLocal, fill_table, get_entry
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
    {"id": 1, "media_id": 1, "bucket_key": "dummy_key", "created_at": "2020-10-13T08:18:45.447773"},
]


MEDIA_TABLE_FOR_DB = list(map(update_only_datetime, MEDIA_TABLE))
ANNOTATIONS_TABLE_FOR_DB = list(map(update_only_datetime, ANNOTATIONS_TABLE))


@pytest.fixture(scope="function")
async def init_test_db(monkeypatch, test_db):
    monkeypatch.setattr(crud.base, "database", test_db)
    monkeypatch.setattr(db, "SessionLocal", TestSessionLocal)
    await fill_table(test_db, db.accesses, ACCESS_TABLE)
    await fill_table(test_db, db.media, MEDIA_TABLE_FOR_DB)
    await fill_table(test_db, db.annotations, ANNOTATIONS_TABLE_FOR_DB)


@pytest.mark.parametrize(
    "access_idx, annotation_id, status_code, status_details",
    [
        [None, 1, 401, "Not authenticated"],
        [0, 1, 403, "This access can't read resources"],
        [1, 1, 200, None],
        [1, 999, 404, "Table annotations has no entry with id=999"],
        [1, 0, 422, None],
    ],
)
@pytest.mark.asyncio
async def test_get_annotation(test_app_asyncio, init_test_db, access_idx, annotation_id, status_code, status_details):

    # Create a custom access token
    auth = None
    if isinstance(access_idx, int):
        auth = await pytest.get_token(ACCESS_TABLE[access_idx]["id"], ACCESS_TABLE[access_idx]["scope"].split())

    response = await test_app_asyncio.get(f"/annotations/{annotation_id}", headers=auth)
    assert response.status_code == status_code
    if isinstance(status_details, str):
        assert response.json()["detail"] == status_details

    if response.status_code // 100 == 2:
        assert response.json() == {k: v for k, v in ANNOTATIONS_TABLE[annotation_id - 1].items() if k != "bucket_key"}


@pytest.mark.parametrize(
    "access_idx, status_code, status_details, expected_results",
    [
        [None, 401, "Not authenticated", None],
        [0, 200, None, []],
        [1, 200, None, [{k: v for k, v in elt.items() if k != "bucket_key"} for elt in ANNOTATIONS_TABLE]],
    ],
)
@pytest.mark.asyncio
async def test_fetch_annotations(
    test_app_asyncio, init_test_db, access_idx, status_code, status_details, expected_results
):

    # Create a custom access token
    auth = None
    if isinstance(access_idx, int):
        auth = await pytest.get_token(ACCESS_TABLE[access_idx]["id"], ACCESS_TABLE[access_idx]["scope"].split())

    response = await test_app_asyncio.get("/annotations/", headers=auth)
    assert response.status_code == status_code
    if isinstance(status_details, str):
        assert response.json()["detail"] == status_details

    if response.status_code // 100 == 2:
        assert response.json() == expected_results


@pytest.mark.parametrize(
    "access_idx, payload, status_code, status_details",
    [
        [None, {"media_id": 1}, 401, "Not authenticated"],
        [0, {"media_id": 1}, 201, None],
        [1, {"media_id": 1}, 201, None],
        [1, {"media_id": "alpha"}, 422, None],
        [1, {}, 422, None],
    ],
)
@pytest.mark.asyncio
async def test_create_annotation(
    test_app_asyncio, init_test_db, test_db, access_idx, payload, status_code, status_details
):

    # Create a custom access token
    auth = None
    if isinstance(access_idx, int):
        auth = await pytest.get_token(ACCESS_TABLE[access_idx]["id"], ACCESS_TABLE[access_idx]["scope"].split())

    utc_dt = datetime.utcnow()
    response = await test_app_asyncio.post("/annotations/", data=json.dumps(payload), headers=auth)
    assert response.status_code == status_code
    if isinstance(status_details, str):
        assert response.json()["detail"] == status_details

    if response.status_code // 100 == 2:
        json_response = response.json()
        test_response = {"id": len(ANNOTATIONS_TABLE) + 1, **payload}
        assert {k: v for k, v in json_response.items() if k != "created_at"} == test_response

        new_annotation = await get_entry(test_db, db.annotations, json_response["id"])
        new_annotation = dict(**new_annotation)

        # Timestamp consistency
        assert new_annotation["created_at"] > utc_dt and new_annotation["created_at"] < datetime.utcnow()


@pytest.mark.parametrize(
    "access_idx, payload, annotation_id, status_code, status_details",
    [
        [None, {"media_id": 1}, 1, 401, "Not authenticated"],
        [0, {"media_id": 1}, 1, 403, "Your access scope is not compatible with this operation."],
        [1, {"media_id": 1}, 1, 200, None],
        [1, {}, 1, 422, None],
        [1, {"media_id": "alpha"}, 1, 422, None],
        [1, {"media_id": 1}, 999, 404, "Table annotations has no entry with id=999"],
        [1, {"media_id": 1}, 0, 422, None],
    ],
)
@pytest.mark.asyncio
async def test_update_annotation(
    test_app_asyncio, init_test_db, test_db, access_idx, payload, annotation_id, status_code, status_details
):

    # Create a custom access token
    auth = None
    if isinstance(access_idx, int):
        auth = await pytest.get_token(ACCESS_TABLE[access_idx]["id"], ACCESS_TABLE[access_idx]["scope"].split())

    response = await test_app_asyncio.put(f"/annotations/{annotation_id}/", data=json.dumps(payload), headers=auth)
    assert response.status_code == status_code
    if isinstance(status_details, str):
        assert response.json()["detail"] == status_details

    if response.status_code // 100 == 2:
        updated_annotation = await get_entry(test_db, db.annotations, annotation_id)
        updated_annotation = dict(**updated_annotation)
        for k, v in updated_annotation.items():
            if k != "bucket_key":
                assert v == payload.get(k, ANNOTATIONS_TABLE_FOR_DB[annotation_id - 1][k])


@pytest.mark.parametrize(
    "access_idx, annotation_id, status_code, status_details",
    [
        [None, 1, 401, "Not authenticated"],
        [0, 1, 403, "Your access scope is not compatible with this operation."],
        [1, 1, 200, None],
        [1, 999, 404, "Table annotations has no entry with id=999"],
        [1, 0, 422, None],
    ],
)
@pytest.mark.asyncio
async def test_delete_annotation(
    test_app_asyncio, init_test_db, access_idx, annotation_id, status_code, status_details
):

    # Create a custom access token
    auth = None
    if isinstance(access_idx, int):
        auth = await pytest.get_token(ACCESS_TABLE[access_idx]["id"], ACCESS_TABLE[access_idx]["scope"].split())

    response = await test_app_asyncio.delete(f"/annotations/{annotation_id}/", headers=auth)
    assert response.status_code == status_code
    if isinstance(status_details, str):
        assert response.json()["detail"] == status_details

    if response.status_code // 100 == 2:
        assert response.json() == {k: v for k, v in ANNOTATIONS_TABLE[annotation_id - 1].items() if k != "bucket_key"}
        remaining_annotation = await test_app_asyncio.get("/annotations/", headers=auth)
        assert all(entry["id"] != annotation_id for entry in remaining_annotation.json())


@pytest.mark.asyncio
async def test_upload_annotation(test_app_asyncio, init_test_db, test_db, monkeypatch):

    admin_idx = 1
    # Create a custom access token
    admin_auth = await pytest.get_token(ACCESS_TABLE[admin_idx]["id"], ACCESS_TABLE[admin_idx]["scope"].split())

    # 1 - Create a annotation that will have an upload
    payload = {"media_id": 2}
    new_annotation_id = len(ANNOTATIONS_TABLE_FOR_DB) + 1
    response = await test_app_asyncio.post("/annotations/", data=json.dumps(payload), headers=admin_auth)
    assert response.status_code == 201

    # 2 - Upload something
    async def mock_upload_file(bucket_key, file_binary):
        return True

    monkeypatch.setattr(annotations_bucket, "upload_file", mock_upload_file)

    # Download and save a temporary file
    local_tmp_path = os.path.join(tempfile.gettempdir(), "my_temp_annotation.json")
    data = {"label": "fire"}
    with open(local_tmp_path, "w") as f:
        json.dump(data, f)

    async def mock_get_file(bucket_key):
        return local_tmp_path

    monkeypatch.setattr(annotations_bucket, "get_file", mock_get_file)

    async def mock_delete_file(filename):
        return True

    monkeypatch.setattr(annotations_bucket, "delete_file", mock_delete_file)

    # Switch content-type from JSON to multipart
    del admin_auth["Content-Type"]

    with open(local_tmp_path, "r") as content:
        response = await test_app_asyncio.post(
            f"/annotations/{new_annotation_id}/upload", files=dict(file=content), headers=admin_auth
        )

    assert response.status_code == 200, print(response.json()["detail"])
    response_json = response.json()
    updated_annotation = await get_entry(test_db, db.annotations, response_json["id"])
    updated_annotation = dict(**updated_annotation)
    response_json.pop("created_at")
    assert {k: v for k, v in updated_annotation.items() if k not in ("created_at", "bucket_key")} == response_json
    assert updated_annotation["bucket_key"] is not None

    # 2b - Upload failing
    async def failing_upload(bucket_key, file_binary):
        return False

    monkeypatch.setattr(annotations_bucket, "upload_file", failing_upload)
    response = await test_app_asyncio.post(
        f"/annotations/{new_annotation_id}/upload", files=dict(file="bar"), headers=admin_auth
    )
    assert response.status_code == 500
