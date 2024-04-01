import json
from datetime import datetime

import pytest
import pytest_asyncio

from app import db
from app.api import crud
from tests.db_utils import TestSessionLocal, fill_table, get_entry
from tests.utils import update_only_datetime

from app.db.models import ObservationType

ACCESS_TABLE = [
    {"id": 1, "login": "first_login", "hashed_password": "hashed_pwd", "scope": "user"},
    {"id": 2, "login": "second_login", "hashed_password": "hashed_pwd", "scope": "admin"},
]

MEDIA_TABLE = [
    {"id": 1, "type": "image", "created_at": "2020-10-13T08:18:45.447773"},
    {"id": 2, "type": "video", "created_at": "2020-10-13T09:18:45.447773"},
]

ANNOTATIONS_TABLE = [
    {"id": 1, "media_id": 1, "observations": [ObservationType.fire, ObservationType.smoke, ObservationType.clouds], "created_at": "2020-10-13T08:18:45.447773"},
    {"id": 2, "media_id": 2, "observations": [], "created_at": "2022-10-13T08:18:45.447773"},
]


MEDIA_TABLE_FOR_DB = list(map(update_only_datetime, MEDIA_TABLE))
ANNOTATIONS_TABLE_FOR_DB = list(map(update_only_datetime, ANNOTATIONS_TABLE))


@pytest_asyncio.fixture(scope="function")
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
        assert response.json() == ANNOTATIONS_TABLE[annotation_id - 1]


@pytest.mark.parametrize(
    "access_idx, status_code, status_details, expected_results",
    [
        [None, 401, "Not authenticated", None],
        [0, 200, None, []],
        [1, 200, None, ANNOTATIONS_TABLE],
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
        [None, {"media_id": 1, "observations": []}, 401, "Not authenticated"],
        [0, {"media_id": 1, "observations": []}, 201, None],
        [1, {"media_id": 1, "observations": []}, 201, None],
        [1, {"media_id": 1, "observations": ["clouds"]}, 201, None],
        [1, {"media_id": 1, "observations": ["clouds", "fire", "smoke"]}, 201, None],
        [1, {"media_id": 1, "observations": ["clouds", "fire", "puppy"]}, 422, None],
        [1, {"media_id": 1, "observations": [1337]}, 422, None],
        [1, {"media_id": 1, "observations": "smoke"}, 422, None],
        [1, {"media_id": "alpha", "observations": []}, 422, None],
        [1, {}, 422, None],
        [1, {"media_id": 1}, 422, None],
        [1, {"observations": []}, 422, None],
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
    response = await test_app_asyncio.post("/annotations/", json=payload, headers=auth)
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
        [None, {"observations": []}, 1, 401, "Not authenticated"],
        [0, {"observations": []}, 1, 403, "Your access scope is not compatible with this operation."],
        [1, {"observations": []}, 1, 200, None],
        [1, {"observations": [1337]}, 1, 422, None],
        [1, {"observations": ["smoke"]}, 1, 200, None],
        [1, {"observations": ["smoke", "fire", "puppy"]}, 1, 422, None],
        [1, {}, 1, 422, None],
        [1, {"observations": "smoke"}, 1, 422, None],
        [1, {"observations": []}, 999, 404, "Table annotations has no entry with id=999"],
        [1, {"observations": []}, 0, 422, None],
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
        assert response.json() == ANNOTATIONS_TABLE[annotation_id - 1]
        remaining_annotation = await test_app_asyncio.get("/annotations/", headers=auth)
        assert all(entry["id"] != annotation_id for entry in remaining_annotation.json())
