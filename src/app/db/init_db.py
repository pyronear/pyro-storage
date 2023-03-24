# Copyright (C) 2022-2023, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

from app import config as cfg
from app.api import crud
from app.api.schemas import AccessCreation, AccessType
from app.api.security import hash_password
from app.db import accesses


async def init_db():

    login = cfg.SUPERUSER_LOGIN

    # check if access login does not already exist
    entry = await crud.fetch_one(accesses, {"login": login})
    if entry is None:

        hashed_password = await hash_password(cfg.SUPERUSER_PWD)

        access = AccessCreation(login=login, hashed_password=hashed_password, scope=AccessType.admin)
        await crud.create_entry(accesses, access)

    return None
