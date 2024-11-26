import pytest
from requests.exceptions import ConnectionError as ConnError
from requests.exceptions import ReadTimeout

from pyroannotationclient.client import Client
from pyroannotationclient.exceptions import HTTPRequestError


@pytest.mark.parametrize(
    ("token", "host", "timeout", "expected_error"),
    [
        ("invalid_token", "http://localhost:5050", 10, HTTPRequestError),
        (pytest.admin_token, "http://localhost:8003", 10, ConnError),
        (pytest.admin_token, "http://localhost:5050", 0.00001, ReadTimeout),
        (pytest.admin_token, "http://localhost:5050", 10, None),
    ],
)
def test_client_constructor(token, host, timeout, expected_error):
    if expected_error is None:
        Client(token, host, timeout=timeout)
    else:
        with pytest.raises(expected_error):
            Client(token, host, timeout=timeout)


def test_agent_workflow(source_token, mock_img):
    source_client = Client(source_token, "http://localhost:5050", timeout=10)
    response = source_client.heartbeat()
    assert response.status_code == 200
    # Check that last_image gets changed
    assert response.json()["last_image"] is None

    # Check that adding bboxes works
    with pytest.raises(ValueError, match="bboxes must be a non-empty list of tuples"):
        source_client.create_detection(mock_img, 123.2, None)
    with pytest.raises(ValueError, match="bboxes must be a non-empty list of tuples"):
        source_client.create_detection(mock_img, 123.2, [])
    response = source_client.create_detection(mock_img, 123.2, [(0, 0, 1.0, 0.9, 0.5)])
    assert response.status_code == 201, response.__dict__
    response = source_client.create_detection(mock_img, 123.2, [(0, 0, 1.0, 0.9, 0.5), (0.2, 0.2, 0.7, 0.7, 0.8)])
    assert response.status_code == 201, response.__dict__
    return response.json()["id"]


def test_user_workflow(user_token):
    # User workflow
    user_client = Client(user_token, "http://localhost:5050", timeout=10)
    response = user_client.fetch_detections()
    assert response.status_code == 200, response.__dict__
    response = user_client.fetch_unlabeled_detections("2018-06-06T00:00:00")
    assert response.status_code == 200
