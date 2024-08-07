# Copyright (C) 2022-2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

import os
import secrets
from typing import List, Optional

PROJECT_NAME: str = "Pyronear - Storage API"
PROJECT_DESCRIPTION: str = "API for wildfire data curation"
API_BASE: str = "storage/"
VERSION: str = "0.1.1.dev0"
DEBUG: bool = os.environ.get("DEBUG", "") != "False"
DATABASE_URL: str = os.getenv("DATABASE_URL", "")
# Fix for SqlAlchemy 1.4+
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL", "")
LOGO_URL: str = "https://pyronear.org/img/logo_letters.png"

SECRET_KEY: str = secrets.token_urlsafe(32)
if DEBUG:
    # To keep the same Auth at every app loading in debug mode and not having to redo the auth.
    debug_secret_key = "000000000000000000000000000000000000"  # nosec B105
    SECRET_KEY = debug_secret_key

ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
ACCESS_TOKEN_UNLIMITED_MINUTES = 60 * 24 * 365 * 10
JWT_ENCODING_ALGORITHM = "HS256"

CORS_ORIGIN: List[str] = os.getenv("CORS_ORIGIN", "*").split(",")

SUPERUSER_LOGIN: str = os.getenv("SUPERUSER_LOGIN", "")
SUPERUSER_PWD: str = os.getenv("SUPERUSER_PWD", "")

if SUPERUSER_LOGIN is None or SUPERUSER_PWD is None:
    raise ValueError(
        "Missing Credentials. Please set 'SUPERUSER_LOGIN' and 'SUPERUSER_PWD' in your environment variables"
    )

BUCKET_NAME: str = os.getenv("BUCKET_NAME", "")
S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "")
S3_REGION: str = os.getenv("S3_REGION", "")
S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "")

DUMMY_BUCKET_FILE = (
    "https://ec.europa.eu/jrc/sites/jrcsh/files/styles/normal-responsive/"
    + "public/growing-risk-future-wildfires_adobestock_199370851.jpeg"
)


# Sentry
SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
SERVER_NAME: Optional[str] = os.getenv("SERVER_NAME")
