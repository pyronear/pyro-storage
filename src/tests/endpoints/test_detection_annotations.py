import json
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

now = datetime.utcnow()


@pytest.mark.asyncio
async def test_create_detection_annotation(async_client: AsyncClient, sequence_session: AsyncSession, mock_img: bytes):
    detection_payload = {
        "sequence_id": "1",
        "alert_api_id": "1",
        "recorded_at": (now - timedelta(days=2)).isoformat(),
        "algo_predictions": json.dumps({
            "predictions": [{"xyxyn": [0.15, 0.15, 0.3, 0.3], "confidence": 0.88, "class_name": "smoke"}]
        }),
    }

    detection_response = await async_client.post(
        "/detections",
        data=detection_payload,
        files={"file": ("image.jpg", mock_img, "image/jpeg")},
    )
    assert detection_response.status_code == 201
    detection_id = detection_response.json()["id"]

    annotation_payload = {
        "detection_id": str(detection_id),
        "source_api": "pyronear_french",
        "alert_api_id": "1",
        "annotation": json.dumps({
            "predictions": [{"xyxyn": [0.1, 0.1, 0.2, 0.2], "confidence": 0.9, "class_name": "smoke"}]
        }),
        "processing_stages": "visual_check",  # Enum sous forme de str
    }

    response = await async_client.post("/dannotations", data=annotation_payload)
    assert response.status_code == 201
    json_response = response.json()
    assert json_response["detection_id"] == detection_id
    assert json_response["processing_stages"] == "visual_check"
    assert "annotation" in json_response


@pytest.mark.asyncio
async def test_list_detection_annotations(async_client: AsyncClient):
    response = await async_client.get("/dannotations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_detection_annotation(async_client: AsyncClient):
    annotation_id = 1
    response = await async_client.get(f"/dannotations/{annotation_id}")
    if response.status_code == 200:
        annotation = response.json()
        assert annotation["id"] == annotation_id
        assert "annotation" in annotation
    else:
        assert response.status_code in (404, 422)


@pytest.mark.asyncio
async def test_update_detection_annotation(async_client: AsyncClient):
    annotation_id = 1
    update_payload = {
        "annotation": {"predictions": [{"xyxyn": [0.2, 0.2, 0.3, 0.3], "confidence": 0.95, "class_name": "fire"}]},
        "processing_stages": "annotated",
    }

    response = await async_client.patch(f"/dannotations/{annotation_id}", json=update_payload)

    if response.status_code == 200:
        json_response = response.json()
        assert json_response["processing_stages"] == "annotated"
        assert json_response["annotation"]["predictions"][0]["class_name"] == "fire"
    else:
        assert response.status_code in (404, 422)


@pytest.mark.asyncio
async def test_delete_detection_annotation(async_client: AsyncClient):
    annotation_id = 1
    delete_response = await async_client.delete(f"/dannotations/{annotation_id}")
    assert delete_response.status_code in (204, 404)

    get_response = await async_client.get(f"/dannotations/{annotation_id}")
    assert get_response.status_code == 404
