# Copyright (C) 2022, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

from app.api.external import post_request


def test_post_request():
    response = post_request("https://httpbin.org/post")
    assert response.status_code == 200
