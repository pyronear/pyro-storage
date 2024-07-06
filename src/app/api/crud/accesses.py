# Copyright (C) 2022-2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

from fastapi import HTTPException, status
from sqlalchemy import Table

from app.api import security
from app.api.crud import base
from app.api.schemas import AccessCreation, AccessRead, Cred, CredHash, Login


async def check_login_existence(table: Table, login: str):
    """Check that the login does not already exist, raises a 400 exception if do so."""
    if await base.fetch_one(table, {"login": login}) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An entry with login='{login}' already exists.",
        )


async def update_login(accesses: Table, login: str, access_id: int):
    """Update access login assuming access_id exists and new login does not exist."""
    return await base.update_entry(accesses, Login(login=login), access_id)


async def post_access(accesses: Table, login: str, password: str, scope: str) -> AccessRead:
    """Insert an access entry in the accesses table, call within a transaction to reuse returned access id."""
    await check_login_existence(accesses, login)

    # Hash the password
    pwd = await security.hash_password(password)

    access = AccessCreation(login=login, hashed_password=pwd, scope=scope)
    entry = await base.create_entry(accesses, access)

    return AccessRead(**entry)


async def update_access_pwd(accesses: Table, payload: Cred, access_id: int) -> None:
    """Update the access password using provided access_id."""
    # Update the access entry with the hashed password
    updated_payload = CredHash(hashed_password=await security.hash_password(payload.password))

    await base.update_entry(accesses, updated_payload, access_id)  # update & check if access_id exists
