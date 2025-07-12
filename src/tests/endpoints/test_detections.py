from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_detection(async_client: AsyncClient, mock_img: bytes):
    payload = {
        "sequence_id": 1,
        "algo_predictions": {
            "predictions": [{"xyxyn": [0.1, 0.1, 0.2, 0.2], "confidence": 0.95, "class_name": "smoke"}]
        },
    }

    response = await async_client.post(
        "/detections",
        data={
            "sequence_id": payload["sequence_id"],
            "algo_predictions": str(payload["algo_predictions"]),
        },
        files={"file": ("image.jpg", mock_img, "image/jpeg")},
    )
    assert response.status_code == 201
    json_response = response.json()
    assert "id" in json_response
    assert json_response["sequence_id"] == payload["sequence_id"]
    assert json_response["algo_predictions"] == payload["algo_predictions"]


@pytest.mark.asyncio
async def test_get_detection(async_client: AsyncClient, detection_id: int = 1):
    response = await async_client.get(f"/detections/{detection_id}")
    if response.status_code == 200:
        detection = response.json()
        assert detection["id"] == detection_id
        assert "algo_predictions" in detection
    else:
        assert response.status_code in (404, 422)


@pytest.mark.asyncio
async def test_get_detection_url(async_client: AsyncClient, detection_id: int = 1):
    response = await async_client.get(f"/detections/{detection_id}/url")
    if response.status_code == 200:
        url_data = response.json()
        assert "url" in url_data
        assert url_data["url"].startswith("http")
    else:
        assert response.status_code in (404, 422)


@pytest.mark.asyncio
async def test_list_detections(async_client: AsyncClient):
    response = await async_client.get("/detections")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_fetch_unlabeled_detections(async_client: AsyncClient):
    # Use a valid datetime in ISO format
    from_date = (datetime.utcnow() - timedelta(days=1)).isoformat()
    response = await async_client.get(f"/detections/unlabeled/fromdate?from_date={from_date}")
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    for det in results:
        assert "url" in det
        assert det["url"].startswith("http")


@pytest.mark.asyncio
async def test_delete_detection(async_client: AsyncClient):
    # First, create a detection
    create_resp = await async_client.post(
        "/detections",
        data={
            "sequence_id": 1,
            "algo_predictions": str({
                "predictions": [{"xyxyn": [0.1, 0.1, 0.2, 0.2], "confidence": 0.95, "class_name": "smoke"}]
            }),
        },
        files={"file": ("image.jpg", b"dummydata", "image/jpeg")},
    )
    assert create_resp.status_code == 201
    detection_id = create_resp.json()["id"]

    # Now delete it
    delete_resp = await async_client.delete(f"/detections/{detection_id}")
    assert delete_resp.status_code == 204

    # Confirm deletion
    get_resp = await async_client.get(f"/detections/{detection_id}")
    assert get_resp.status_code == 404
