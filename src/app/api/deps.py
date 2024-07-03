# Copyright (C) 2022-2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from pydantic import ValidationError

import app.config as cfg
from app.api import crud
from app.api.schemas import AccessRead, AccessType, TokenPayload
from app.db import accesses

# Scope definition
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login/access-token",
    scopes={
        AccessType.user: "Read information about the current user.",
        AccessType.admin: "Admin rights on all routes.",
    },
)


async def get_current_access(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)) -> AccessRead:
    """Dependency to use as fastapi.security.Security with scopes.

    >>> @app.get("/users/me")
    >>> async def read_users_me(current_user: User = Security(get_current_access, scopes=["me"])):
    >>>     return current_user
    """

    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    try:
        payload = jwt.decode(token, cfg.SECRET_KEY, algorithms=[cfg.JWT_ENCODING_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": authenticate_value},
        )

    try:
        access_id = int(payload["sub"])
        token_scopes = payload.get("scopes", [])
        token_data = TokenPayload(access_id=access_id, scopes=token_scopes)
    except (KeyError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid token payload.",
            headers={"WWW-Authenticate": authenticate_value},
        )

    entry = await crud.get_entry(table=accesses, entry_id=int(access_id))

    if set(token_data.scopes).isdisjoint(security_scopes.scopes):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your access scope is not compatible with this operation.",
            headers={"WWW-Authenticate": authenticate_value},
        )

    return AccessRead(**entry)
