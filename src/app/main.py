# Copyright (C) 2022-2023, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

import logging
import time

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from app import config as cfg
from app.api.routes import accesses, annotations, login, media
from app.db import database, engine, init_db, metadata

logger = logging.getLogger("uvicorn.error")

metadata.create_all(bind=engine)

# Sentry
if isinstance(cfg.SENTRY_DSN, str):
    sentry_sdk.init(
        cfg.SENTRY_DSN,
        release=cfg.VERSION,
        server_name=cfg.SERVER_NAME,
        environment="production" if isinstance(cfg.SERVER_NAME, str) else None,
        traces_sample_rate=0.0,
    )
    logger.info(f"Sentry middleware enabled on server {cfg.SERVER_NAME}")


app = FastAPI(title=cfg.PROJECT_NAME, description=cfg.PROJECT_DESCRIPTION, debug=cfg.DEBUG, version=cfg.VERSION)


# Database connection
@app.on_event("startup")
async def startup():
    await database.connect()
    await init_db()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


# Routing
app.include_router(login.router, prefix="/login", tags=["login"])
app.include_router(media.router, prefix="/media", tags=["media"])
app.include_router(annotations.router, prefix="/annotations", tags=["annotations"])
app.include_router(accesses.router, prefix="/accesses", tags=["accesses"])


# Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


if isinstance(cfg.SENTRY_DSN, str):
    app.add_middleware(SentryAsgiMiddleware)


# Docs
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=cfg.PROJECT_NAME,
        version=cfg.VERSION,
        description=cfg.PROJECT_DESCRIPTION,
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {"url": cfg.LOGO_URL}
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[assignment]
