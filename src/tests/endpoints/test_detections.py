from typing import Any, Dict, List, Union

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession


@pytest.mark.parametrize(
    ("user_idx", "source_idx", "payload", "status_code", "status_detail"),
    [
        (None, None, {"azimuth": 45.6, "bboxes_prediction": "[(0.6,0.6,0.7,0.7,0.6)]"}, 401, "Not authenticated"),
        (0, None, {"azimuth": 45.6, "bboxes_prediction": "[(0.6,0.6,0.7,0.7,0.6)]"}, 403, "Incompatible token scope."),
        (
            1,
            None,
            {
                "azimuth": 45.6,
                "bboxes_prediction": "[(0.6,0.6,0.7,0.7,0.6)]",
                "annotation_id": None,
                "bbox_auto": None,
                "bbox_verified": None,
                "prediction": None,
            },
            201,
            None,
        ),
        (2, None, {"azimuth": 45.6, "bboxes_prediction": "[(0.6,0.6,0.7,0.7,0.6)]"}, 403, "Incompatible token scope."),
        (None, 0, {"azimuth": "hello"}, 422, None),
        (None, 0, {}, 422, None),
        (None, 0, {"azimuth": 45.6, "bboxes_prediction": []}, 422, None),
        (None, 1, {"azimuth": 45.6, "bboxes_prediction": (0.6, 0.6, 0.6, 0.6, 0.6)}, 422, None),
        (None, 1, {"azimuth": 45.6, "bboxes_prediction": "[(0.6, 0.6, 0.6, 0.6, 0.6)]"}, 422, None),
        (
            None,
            1,
            {
                "azimuth": 45.6,
                "bboxes_prediction": "[(0.6,0.6,0.7,0.7,0.6)]",
                "annotation_id": None,
                "bbox_auto": None,
                "bbox_verified": None,
                "prediction": None,
            },
            201,
            None,
        ),
    ],
)
@pytest.mark.asyncio
async def test_create_detection(
    async_client: AsyncClient,
    detection_session: AsyncSession,
    mock_img: bytes,
    user_idx: Union[int, None],
    source_idx: Union[int, None],
    payload: Dict[str, Any],
    status_code: int,
    status_detail: Union[str, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = pytest.get_token(
            pytest.user_table[user_idx]["id"],
            pytest.user_table[user_idx]["role"].split(),
            pytest.user_table[user_idx]["source_id"],
        )
    elif isinstance(source_idx, int):
        auth = pytest.get_token(
            pytest.source_table[source_idx]["id"],
            ["agent"],
            pytest.source_table[source_idx]["id"],
        )

    response = await async_client.post(
        "/detections", data=payload, files={"file": ("logo.png", mock_img, "image/png")}, headers=auth
    )
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert {
            k: v
            for k, v in response.json().items()
            if k not in {"created_at", "updated_at", "id", "bucket_key", "source_id"}
        } == payload
        assert response.json()["id"] == max(entry["id"] for entry in pytest.detection_table) + 1
        if source_idx is not None:
            assert response.json()["source_id"] == pytest.source_table[source_idx]["id"]


@pytest.mark.parametrize(
    ("user_idx", "detection_id", "status_code", "status_detail", "expected_idx"),
    [
        (None, 1, 401, "Not authenticated", None),
        (0, 0, 422, None, None),
        (0, 10, 404, "Table Detection has no corresponding entry.", None),
        (0, 1, 200, None, 0),
        (0, 2, 200, None, 1),
        (1, 1, 200, None, 0),
        (1, 2, 200, None, 1),
    ],
)
@pytest.mark.asyncio
async def test_get_detection(
    async_client: AsyncClient,
    detection_session: AsyncSession,
    user_idx: Union[int, None],
    detection_id: int,
    status_code: int,
    status_detail: Union[str, None],
    expected_idx: Union[int, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = pytest.get_token(
            pytest.user_table[user_idx]["id"],
            pytest.user_table[user_idx]["role"].split(),
            pytest.user_table[user_idx]["source_id"],
        )

    response = await async_client.get(f"/detections/{detection_id}", headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() == pytest.detection_table[expected_idx]


@pytest.mark.parametrize(
    ("user_idx", "status_code", "status_detail", "expected_result"),
    [
        (None, 401, "Not authenticated", None),
        (0, 200, None, pytest.detection_table),
        (1, 200, None, [pytest.detection_table[0], pytest.detection_table[1]]),
    ],
)
@pytest.mark.asyncio
async def test_fetch_detections(
    async_client: AsyncClient,
    detection_session: AsyncSession,
    user_idx: Union[int, None],
    status_code: int,
    status_detail: Union[str, None],
    expected_result: Union[List[Dict[str, Any]], None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = pytest.get_token(
            pytest.user_table[user_idx]["id"],
            pytest.user_table[user_idx]["role"].split(),
            pytest.user_table[user_idx]["source_id"],
        )

    response = await async_client.get("/detections", headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() == expected_result


@pytest.mark.parametrize(
    ("user_idx", "from_date", "status_code", "status_detail", "expected_result"),
    [
        (None, "2018-06-06T00:00:00", 401, "Not authenticated", None),
        (0, "", 422, None, None),
        (0, "old-date", 422, None, None),
        (0, "2018-19-20T00:00:00", 422, None, None),  # impossible date
        (0, "2018-06-06", 422, None, None),  # datetime != date
        (1, "2018-06-06T00:00:00", 200, None, []),
        (2, "2018-06-06T00:00:00", 200, None, [pytest.detection_table[2]]),
    ],
)
@pytest.mark.asyncio
async def test_fetch_unlabeled_detections(
    async_client: AsyncClient,
    detection_session: AsyncSession,
    user_idx: Union[int, None],
    from_date: str,
    status_code: int,
    status_detail: Union[str, None],
    expected_result: Union[List[Dict[str, Any]], None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = pytest.get_token(
            pytest.user_table[user_idx]["id"],
            pytest.user_table[user_idx]["role"].split(),
            pytest.user_table[user_idx]["source_id"],
        )

    response = await async_client.get(f"/detections/unlabeled/fromdate?from_date={from_date}", headers=auth)

    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert [{k: v for k, v in det.items() if k != "url"} for det in response.json()] == expected_result
        assert all(det["url"].startswith("http://") for det in response.json())


@pytest.mark.parametrize(
    ("user_idx", "detection_id", "payload", "status_code", "status_detail", "expected_idx"),
    [
        (None, 1, {"label": "wildfire"}, 401, "Not authenticated", None),
        (0, 0, {"label": "wildfire"}, 422, None, None),
        (0, 1, {"label": "hello"}, 422, None, None),
        (0, 1, {"label": "wildfire"}, 200, None, 0),
        (2, 3, {"label": "wildfire"}, 200, None, 1),
        (1, 1, {"label": "wildfire"}, 200, None, 0),
        (2, 3, {"label": "nothing"}, 200, None, 1),
        (2, 1, {"label": "wildfire"}, 403, None, 0),
    ],
)
@pytest.mark.asyncio
async def test_label_detection(
    async_client: AsyncClient,
    detection_session: AsyncSession,
    user_idx: Union[int, None],
    detection_id: int,
    payload: Dict[str, Any],
    status_code: int,
    status_detail: Union[str, None],
    expected_idx: Union[int, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = pytest.get_token(
            pytest.user_table[user_idx]["id"],
            pytest.user_table[user_idx]["role"].split(),
            pytest.user_table[user_idx]["source_id"],
        )

    response = await async_client.patch(f"/detections/{detection_id}/label", json=payload, headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() == {
            **{k: v for k, v in pytest.annotation_table[expected_idx].items() if k != "label"},
            **payload,
        }


@pytest.mark.parametrize(
    ("user_idx", "detection_id", "status_code", "status_detail"),
    [
        (None, 1, 401, "Not authenticated"),
        (0, 100, 404, "Table Detection has no corresponding entry."),
        (0, 1, 200, None),
        (1, 1, 200, None),
        (2, 1, 403, "Access forbidden."),
    ],
)
@pytest.mark.asyncio
async def test_get_detection_url(
    async_client: AsyncClient,
    detection_session: AsyncSession,
    mock_img: bytes,
    user_idx: Union[int, None],
    detection_id: Union[int, None],
    status_code: int,
    status_detail: Union[str, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = pytest.get_token(
            pytest.user_table[user_idx]["id"],
            pytest.user_table[user_idx]["role"].split(),
            pytest.user_table[user_idx]["source_id"],
        )

    response = await async_client.get(f"/detections/{detection_id}/url", headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert isinstance(response.json()["url"], str)
        assert response.json()["url"].startswith("http://")


@pytest.mark.parametrize(
    ("user_idx", "detection_id", "status_code", "status_detail"),
    [
        (None, 1, 401, "Not authenticated"),
        (0, 0, 422, None),
        (0, 100, 404, "Table Detection has no corresponding entry."),
        (0, 1, 200, None),
        (0, 2, 200, None),
        (1, 1, 403, None),
        (1, 2, 403, None),
    ],
)
@pytest.mark.asyncio
async def test_delete_detection(
    async_client: AsyncClient,
    detection_session: AsyncSession,
    user_idx: Union[int, None],
    detection_id: int,
    status_code: int,
    status_detail: Union[str, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = pytest.get_token(
            pytest.user_table[user_idx]["id"],
            pytest.user_table[user_idx]["role"].split(),
            pytest.user_table[user_idx]["source_id"],
        )

    response = await async_client.delete(f"/detections/{detection_id}", headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() is None


@pytest.mark.parametrize(
    ("user_idx", "detection_id", "payload", "status_code", "status_detail", "expected_idx"),
    [
        (None, 1, {"bbox_auto": "[(.1,.1,.7,.8,.9)]"}, 401, "Not authenticated", None),
        (0, 0, {"bbox_auto": "[(.1,.1,.7,.8,.9)]"}, 422, None, None),
        (0, 1, {"bbox_auto": "[(.1,.1,.7,.8,.9)]"}, 200, None, 0),
        (2, 3, {"bbox_auto": "[(.1,.1,.7,.8,.9)]"}, 403, None, None),
        (1, 1, {"bbox_auto": "[(.1,.1,.7,.8,.9)]"}, 200, None, 0),
        (2, 1, {"bbox_auto": "[(.1,.1,.7,.8,.9)]"}, 403, None, None),
    ],
)
@pytest.mark.asyncio
async def test_update_bbox_detection(
    async_client: AsyncClient,
    detection_session: AsyncSession,
    user_idx: Union[int, None],
    detection_id: int,
    payload: Dict[str, Any],
    status_code: int,
    status_detail: Union[str, None],
    expected_idx: Union[int, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = pytest.get_token(
            pytest.user_table[user_idx]["id"],
            pytest.user_table[user_idx]["role"].split(),
            pytest.user_table[user_idx]["source_id"],
        )

    response = await async_client.patch(f"/detections/{detection_id}/update", json=payload, headers=auth)

    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() == {
            **{k: v for k, v in pytest.detection_table[expected_idx].items() if k != "bbox_auto"},
            **payload,
        }


@pytest.mark.parametrize(
    ("user_idx", "detection_id", "payload", "status_code", "status_detail", "expected_idx"),
    [
        (None, 1, {"bbox_verified": "[(.1,.1,.7,.8,.9)]"}, 401, "Not authenticated", None),
        (0, 0, {"bbox_verified": "[(.1,.1,.7,.8,.9)]"}, 422, None, None),
        (0, 1, {"bbox_verified": "[(.1,.1,.7,.8,.9)]"}, 200, None, 0),
        (1, 3, {"bbox_verified": "[(.1,.1,.7,.8,.9)]"}, 403, None, None),
        (2, 1, {"bbox_verified": "[(.1,.1,.7,.8,.9)]"}, 403, None, 0),
        (2, 3, {"bbox_verified": "[(.1,.1,.7,.8,.9)]"}, 200, None, 2),
        (1, 1, {"bbox_verified": "[(.1,.1,.7,.8,.9)]"}, 403, None, None),
    ],
)
@pytest.mark.asyncio
async def test_update_bbox_verified(
    async_client: AsyncClient,
    detection_session: AsyncSession,
    user_idx: Union[int, None],
    detection_id: int,
    payload: Dict[str, Any],
    status_code: int,
    status_detail: Union[str, None],
    expected_idx: Union[int, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = pytest.get_token(
            pytest.user_table[user_idx]["id"],
            pytest.user_table[user_idx]["role"].split(),
            pytest.user_table[user_idx]["source_id"],
        )

    response = await async_client.patch(f"/detections/{detection_id}/updateverified", json=payload, headers=auth)

    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() == {
            **{k: v for k, v in pytest.detection_table[expected_idx].items() if k != "bbox_verified"},
            **payload,
        }
