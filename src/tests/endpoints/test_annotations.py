from typing import Any, Dict, Union

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession


@pytest.mark.parametrize(
    ("user_idx", "payload", "status_code", "status_detail"),
    [
        (None, {"gif_url": "habile.com", "label": "wildfire"}, 401, "Not authenticated"),
        (0, {"gif_url": "habile.com", "label": "wildfire"}, 201, None),
        (
            1,
            {"gif_url": "habile.com", "label": "wildfire"},
            201,
            None,
        ),
        (2, {"gif_url": "habile.com", "label": "wildfire"}, 201, None),
        (1, {"gif_url": "hello"}, 422, None),
        (1, {}, 422, None),
    ],
)
@pytest.mark.asyncio
async def test_create_annotation(
    async_client: AsyncClient,
    annotation_session: AsyncSession,
    user_idx: Union[int, None],
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

    response = await async_client.post("/annotations", data=payload, headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert {
            k: v
            for k, v in response.json().items()
            if k not in {"created_at", "updated_at", "id", "bucket_key", "source_id"}
        } == payload
        assert response.json()["id"] == max(entry["id"] for entry in pytest.annotation_table) + 1
