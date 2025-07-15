from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
import json

@pytest.mark.asyncio
async def test_create_detection(async_client: AsyncClient, sequence_session: AsyncSession, mock_img: bytes):
    payload = {
        "sequence_id": 1,
        "algo_predictions": {
            "predictions": [{"xyxyn": [0.1, 0.1, 0.2, 0.2], "confidence": 0.95, "class_name": "smoke"}]
        },
    }

    response = await async_client.post(
        "/detections",
        data={
            "sequence_id": str(payload["sequence_id"]),
            "algo_predictions": json.dumps(payload["algo_predictions"]),
        },
        files={"file": ("image.jpg", mock_img, "image/jpeg")},
    )
    print(response.text)
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
async def test_delete_detection(async_client: AsyncClient, sequence_session: AsyncSession, mock_img: bytes):
    # First, create a detection
    payload = {
        "sequence_id": 1,
        "algo_predictions": {
            "predictions": [{"xyxyn": [0.1, 0.1, 0.2, 0.2], "confidence": 0.95, "class_name": "smoke"}]
        },
    }

    response = await async_client.post(
        "/detections",
        data={
            "sequence_id": str(payload["sequence_id"]),
            "algo_predictions": json.dumps(payload["algo_predictions"]),
        },
        files={"file": ("image.jpg", mock_img, "image/jpeg")},
    )
    assert response.status_code == 201
    detection_id = response.json()["id"]

    # Now delete it
    delete_resp = await async_client.delete(f"/detections/{detection_id}")
    assert delete_resp.status_code == 204

    # Confirm deletion
    get_resp = await async_client.get(f"/detections/{detection_id}")
    assert get_resp.status_code == 404
