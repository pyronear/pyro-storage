import json
import os
import tempfile
from datetime import datetime

import pytest
import pytest_asyncio
import requests

from app import db
from app.api import crud
from app.api.security import hash_content_file
from app.services import s3_bucket
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


MEDIA_TABLE_FOR_DB = list(map(update_only_datetime, MEDIA_TABLE))


@pytest_asyncio.fixture(scope="function")
async def init_test_db(monkeypatch, test_db):
    monkeypatch.setattr(crud.base, "database", test_db)
    monkeypatch.setattr(db, "SessionLocal", TestSessionLocal)
    await fill_table(test_db, db.accesses, ACCESS_TABLE)
    await fill_table(test_db, db.media, MEDIA_TABLE_FOR_DB)


@pytest.mark.parametrize(
    "access_idx, media_id, status_code, status_details",
    [
        [None, 1, 401, "Not authenticated"],
        [0, 1, 403, "This access can't read resources"],
        [1, 1, 200, None],
        [1, 999, 404, "Table media has no entry with id=999"],
        [1, 0, 422, None],
    ],
)
@pytest.mark.asyncio
async def test_get_media(test_app_asyncio, init_test_db, access_idx, media_id, status_code, status_details):

    # Create a custom access token
    auth = None
    if isinstance(access_idx, int):
        auth = await pytest.get_token(ACCESS_TABLE[access_idx]["id"], ACCESS_TABLE[access_idx]["scope"].split())

    response = await test_app_asyncio.get(f"/media/{media_id}", headers=auth)
    assert response.status_code == status_code
    if isinstance(status_details, str):
        assert response.json()["detail"] == status_details

    if response.status_code // 100 == 2:
        assert response.json() == MEDIA_TABLE[media_id - 1]


@pytest.mark.parametrize(
    "access_idx, status_code, status_details, expected_results",
    [
        [None, 401, "Not authenticated", None],
        [0, 200, None, []],
        [1, 200, None, MEDIA_TABLE],
    ],
)
@pytest.mark.asyncio
async def test_fetch_media(test_app_asyncio, init_test_db, access_idx, status_code, status_details, expected_results):

    # Create a custom access token
    auth = None
    if isinstance(access_idx, int):
        auth = await pytest.get_token(ACCESS_TABLE[access_idx]["id"], ACCESS_TABLE[access_idx]["scope"].split())

    response = await test_app_asyncio.get("/media/", headers=auth)
    assert response.status_code == status_code
    if isinstance(status_details, str):
        assert response.json()["detail"] == status_details

    if response.status_code // 100 == 2:
        assert response.json() == expected_results


@pytest.mark.parametrize(
    "access_idx, payload, status_code, status_details",
    [
        [None, {}, 401, "Not authenticated"],
        [0, {"type": "video"}, 403, "Your access scope is not compatible with this operation."],
        [1, {}, 201, None],
        [1, {"type": "audio"}, 422, None],
    ],
)
@pytest.mark.asyncio
async def test_create_media(test_app_asyncio, init_test_db, test_db, access_idx, payload, status_code, status_details):

    # Create a custom access token
    auth = None
    if isinstance(access_idx, int):
        auth = await pytest.get_token(ACCESS_TABLE[access_idx]["id"], ACCESS_TABLE[access_idx]["scope"].split())

    utc_dt = datetime.utcnow()
    response = await test_app_asyncio.post("/media/", data=json.dumps(payload), headers=auth)
    assert response.status_code == status_code
    if isinstance(status_details, str):
        assert response.json()["detail"] == status_details

    if response.status_code // 100 == 2:
        json_response = response.json()
        test_response = {"id": len(MEDIA_TABLE) + 1, **payload, "type": "image"}
        assert {k: v for k, v in json_response.items() if k != "created_at"} == test_response

        new_media = await get_entry(test_db, db.media, json_response["id"])
        new_media = dict(**new_media)

        # Timestamp consistency
        assert new_media["created_at"] > utc_dt and new_media["created_at"] < datetime.utcnow()


@pytest.mark.parametrize(
    "access_idx, payload, media_id, status_code, status_details",
    [
        [None, {}, 1, 401, "Not authenticated"],
        [0, {"type": "video"}, 1, 403, "Your access scope is not compatible with this operation."],
        [1, {"type": "video"}, 1, 200, None],
        [1, {"type": "audio"}, 1, 422, None],
        [1, {"type": "image"}, 999, 404, "Table media has no entry with id=999"],
        [1, {"type": "audio"}, 1, 422, None],
        [1, {"type": "image"}, 0, 422, None],
    ],
)
@pytest.mark.asyncio
async def test_update_media(
    test_app_asyncio, init_test_db, test_db, access_idx, payload, media_id, status_code, status_details
):

    # Create a custom access token
    auth = None
    if isinstance(access_idx, int):
        auth = await pytest.get_token(ACCESS_TABLE[access_idx]["id"], ACCESS_TABLE[access_idx]["scope"].split())

    response = await test_app_asyncio.put(f"/media/{media_id}/", data=json.dumps(payload), headers=auth)
    assert response.status_code == status_code
    if isinstance(status_details, str):
        assert response.json()["detail"] == status_details

    if response.status_code // 100 == 2:
        updated_media = await get_entry(test_db, db.media, media_id)
        updated_media = dict(**updated_media)
        for k, v in updated_media.items():
            if k != "bucket_key":
                assert v == payload.get(k, MEDIA_TABLE_FOR_DB[media_id - 1][k])


@pytest.mark.parametrize(
    "access_idx, media_id, status_code, status_details",
    [
        [None, 1, 401, "Not authenticated"],
        [0, 1, 403, "Your access scope is not compatible with this operation."],
        [1, 1, 200, None],
        [1, 999, 404, "Table media has no entry with id=999"],
        [1, 0, 422, None],
    ],
)
@pytest.mark.asyncio
async def test_delete_media(test_app_asyncio, init_test_db, access_idx, media_id, status_code, status_details):

    # Create a custom access token
    auth = None
    if isinstance(access_idx, int):
        auth = await pytest.get_token(ACCESS_TABLE[access_idx]["id"], ACCESS_TABLE[access_idx]["scope"].split())

    response = await test_app_asyncio.delete(f"/media/{media_id}/", headers=auth)
    assert response.status_code == status_code
    if isinstance(status_details, str):
        assert response.json()["detail"] == status_details

    if response.status_code // 100 == 2:
        assert response.json() == MEDIA_TABLE[media_id - 1]
        remaining_media = await test_app_asyncio.get("/media/", headers=auth)
        assert all(entry["id"] != media_id for entry in remaining_media.json())


@pytest.mark.asyncio
async def test_upload_media(test_app_asyncio, init_test_db, test_db, monkeypatch):

    admin_idx = 1
    # Create a custom access token
    admin_auth = await pytest.get_token(ACCESS_TABLE[admin_idx]["id"], ACCESS_TABLE[admin_idx]["scope"].split())

    # 1 - Create a media that will have an upload
    payload = {}
    new_media_id = len(MEDIA_TABLE_FOR_DB) + 1
    response = await test_app_asyncio.post("/media/", data=json.dumps(payload), headers=admin_auth)
    assert response.status_code == 201

    # 2 - Upload something
    async def mock_upload_file(bucket_key, file_binary):
        return True

    monkeypatch.setattr(s3_bucket, "upload_file", mock_upload_file)

    # Download and save a temporary file
    local_tmp_path = os.path.join(tempfile.gettempdir(), "my_temp_image.jpg")
    img_content = requests.get("https://pyronear.org/img/logo_letters.png").content
    with open(local_tmp_path, "wb") as f:
        f.write(img_content)

    md5_hash = hash_content_file(img_content, use_md5=True)

    async def mock_get_file_metadata(bucket_key):
        return {"ETag": md5_hash}

    monkeypatch.setattr(s3_bucket, "get_file_metadata", mock_get_file_metadata)

    async def mock_delete_file(filename):
        return True

    monkeypatch.setattr(s3_bucket, "delete_file", mock_delete_file)

    # Switch content-type from JSON to multipart
    del admin_auth["Content-Type"]

    response = await test_app_asyncio.post(
        f"/media/{new_media_id}/upload", files=dict(file=img_content), headers=admin_auth
    )

    assert response.status_code == 200, print(response.json()["detail"])
    response_json = response.json()
    updated_media = await get_entry(test_db, db.media, response_json["id"])
    updated_media = dict(**updated_media)
    response_json.pop("created_at")
    assert {k: v for k, v in updated_media.items() if k not in ("created_at", "bucket_key")} == response_json
    assert updated_media["bucket_key"] is not None

    # 2b - Upload failing
    async def failing_upload(bucket_key, file_binary):
        return False

    monkeypatch.setattr(s3_bucket, "upload_file", failing_upload)
    response = await test_app_asyncio.post(f"/media/{new_media_id}/upload", files=dict(file="bar"), headers=admin_auth)
    assert response.status_code == 500
