import os
from urllib.parse import urljoin

import pytest
import requests

API_URL = os.getenv("API_URL", "http://localhost:5050/api/v1/")
SUPERADMIN_LOGIN = os.getenv("SUPERADMIN_LOGIN", "superadmin_login")
SUPERADMIN_PWD = os.getenv("SUPERADMIN_PWD", "superadmin_pwd")
SUPERADMIN_TOKEN = requests.post(
    urljoin(API_URL, "login/creds"),
    data={"username": SUPERADMIN_LOGIN, "password": SUPERADMIN_PWD},
    timeout=5,
).json()["access_token"]


def pytest_configure():
    # api.security patching
    pytest.admin_token = SUPERADMIN_TOKEN


@pytest.fixture(scope="session")
def mock_img():
    # Get Pyronear logo
    return requests.get("https://avatars.githubusercontent.com/u/61667887?s=200&v=4", timeout=5).content







