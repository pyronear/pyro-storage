# Copyright (C) 2022-2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

from fastapi import HTTPException, status

from app.api import crud
from app.api.schemas import AccessType
from app.db import accesses


async def is_admin_access(access_id: int) -> bool:
    access = await crud.base.get_entry(accesses, access_id)
    return access["scope"] == AccessType.admin


async def check_access_read(access_id: int) -> bool:
    if not (await is_admin_access(access_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This access can't read resources")
    return True
