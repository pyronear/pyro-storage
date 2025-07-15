from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient

now = datetime.utcnow()


@pytest.mark.asyncio
async def test_create_sequence(async_client: AsyncClient):
    payload = {
        "source_api": "pyronear_french",
        "alert_api_id": "1",
        "camera_name": "test_cam",
        "camera_id": "1",
        "organisation_name": "test_org",
        "organisation_id": "1",
        "is_wildfire_alertapi": "true",
        "azimuth": "90",
        "lat": "0.0",
        "lon": "0.0",
        "created_at": (now - timedelta(days=1)).isoformat(),
        "last_seen_at": now.isoformat(),
    }

    response = await async_client.post("/sequences", data=payload)
    assert response.status_code == 201
    sequence = response.json()
    assert "id" in sequence
    assert sequence["source_api"] == payload["source_api"]
    assert sequence["is_wildfire_alertapi"] is True
    assert sequence["camera_name"] == payload["camera_name"]


@pytest.mark.asyncio
async def test_get_sequence(async_client: AsyncClient):
    sequence_id = 1
    response = await async_client.get(f"/sequences/{sequence_id}")
    if response.status_code == 200:
        seq = response.json()
        assert seq["id"] == sequence_id
        assert "camera_name" in seq
    else:
        assert response.status_code in (404, 422)


@pytest.mark.asyncio
async def test_list_sequences(async_client: AsyncClient):
    response = await async_client.get("/sequences")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_delete_sequence(async_client: AsyncClient, sequence_session):
    sequence_id = 1
    delete_response = await async_client.delete(f"/sequences/{sequence_id}")
    assert delete_response.status_code in (204, 404)

    get_response = await async_client.get(f"/sequences/{sequence_id}")
    assert get_response.status_code == 404
