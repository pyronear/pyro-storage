import time
from copy import deepcopy

import pytest
from requests import ConnectionError

from pyrostorage import client
from pyrostorage.exceptions import HTTPRequestException


def _test_route_return(response, return_type, status_code=200):
    assert response.status_code == status_code
    assert isinstance(response.json(), return_type)

    return response.json()


def test_client():

    # Wrong credentials
    with pytest.raises(HTTPRequestException):
        client.Client("http://localhost:8080", "invalid_login", "invalid_pwd")

    # Incorrect URL port
    with pytest.raises(ConnectionError):
        client.Client("http://localhost:8003", "dummy_login", "dummy_pwd")

    api_client = client.Client("http://localhost:8080", "dummy_login", "dummy_pwd")

    # Media
    media_id = _test_route_return(api_client.create_media(media_type="image"), dict, 201)["id"]
    # Annotation
    _test_route_return(api_client.create_annotation(media_id=media_id, observations=["smoke", "fire"]), dict, 201)["id"]

    # Check token refresh
    prev_headers = deepcopy(api_client.headers)
    # In case the 2nd token creation request is done in the same second, since the expiration is truncated to the
    # second, it returns the same token
    time.sleep(1)
    api_client.refresh_token("dummy_login", "dummy_pwd")
    assert prev_headers != api_client.headers
