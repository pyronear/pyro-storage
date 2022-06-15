# Copyright (C) 2022, Pyronear.

# This program is licensed under the Apache License version 2.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0.txt> for full license details.

import io
import logging
from typing import Dict
from urllib.parse import urljoin

import requests
from requests.models import Response

from .exceptions import HTTPRequestException

__all__ = ["Client"]

logging.basicConfig()

ROUTES: Dict[str, str] = {
    "token": "/login/access-token",
    #################
    # MEDIA
    #################
    "create-media": "/media",
    "upload-media": "/media/{media_id}/upload",
    "get-media-url": "/media/{media_id}/url",
    #################
    # ANNOTATIONS
    #################
    "create-annotation": "/annotations",
    "upload-annotation": "/annotations/{annotation_id}/upload",
    "get-annotation-url": "/annotations/{annotation_id}/url",
}


class Client:
    """Client class to interact with the PyroNear API

    Args:
        api_url (str): url of the pyronear API
        credentials_login (str): Login (e.g: username)
        credentials_password (str): Password (e.g: 123456 (don't do this))
    """

    api: str
    routes: Dict[str, str]
    token: str

    def __init__(self, api_url: str, credentials_login: str, credentials_password: str) -> None:
        self.api = api_url
        # Prepend API url to each route
        self.routes = {k: urljoin(self.api, v) for k, v in ROUTES.items()}
        self.refresh_token(credentials_login, credentials_password)

    @property
    def headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def refresh_token(self, login: str, password: str) -> None:
        self.token = self._retrieve_token(login, password)

    def _retrieve_token(self, login: str, password: str) -> str:
        response = requests.post(
            self.routes["token"],
            data=f"username={login}&password={password}",
            headers={"Content-Type": "application/x-www-form-urlencoded", "accept": "application/json"},
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            # Anyone has a better suggestion?
            raise HTTPRequestException(response.status_code, response.text)

    def create_media(self, media_type: str = "image") -> Response:
        """Create a media entry

        Example::
            >>> from pyrostorage import client
            >>> api_client = client.Client("http://pyro-storage.herokuapp.com", "MY_LOGIN", "MY_PWD")
            >>> response = api_client.create_media(media_type="image")

        Args:
            media_type: the type of media ('image', or 'video')

        Returns:
            HTTP response containing the created media
        """

        return requests.post(self.routes["create-media"], headers=self.headers, json={"type": media_type})

    def upload_media(self, media_id: int, media_data: bytes) -> Response:
        """Upload the media content

        Example::
            >>> from pyrostorage import client
            >>> api_client = client.Client("http://pyro-storage.herokuapp.com", "MY_LOGIN", "MY_PWD")
            >>> with open("path/to/my/file.ext", "rb") as f: data = f.read()
            >>> response = api_client.upload_media(media_id=1, media_data=data)

        Args:
            media_id: ID of the associated media entry
            media_data: byte data

        Returns:
            HTTP response containing the updated media
        """

        return requests.post(
            self.routes["upload-media"].format(media_id=media_id),
            headers=self.headers,
            files={"file": io.BytesIO(media_data)},
        )

    def get_media_url(self, media_id: int) -> Response:
        """Get the image as a URL

        Example::
            >>> from pyrostorage import client
            >>> api_client = client.Client("http://pyro-storage.herokuapp.com", "MY_LOGIN", "MY_PWD")
            >>> response = api_client.get_media_url(1)

        Args:
            media_id: the identifier of the media entry

        Returns:
            HTTP response containing the URL to the media content
        """

        return requests.get(self.routes["get-media-url"].format(media_id=media_id), headers=self.headers)

    def create_annotation(self, media_id: int) -> Response:
        """Create an annotation entry

        Example::
            >>> from pyrostorage import client
            >>> api_client = client.Client("http://pyro-storage.herokuapp.com", "MY_LOGIN", "MY_PWD")
            >>> response = api_client.create_annotation(media_id=1)

        Args:
            media_id: the identifier of the media entry

        Returns:
            HTTP response containing the created annotation
        """

        return requests.post(self.routes["create-annotation"], headers=self.headers, json={"media_id": media_id})

    def upload_annotation(self, annotation_id: int, annotation_data: bytes) -> Response:
        """Upload the annotation content

        Example::
            >>> from pyrostorage import client
            >>> api_client = client.Client("http://pyro-storage.herokuapp.com", "MY_LOGIN", "MY_PWD")
            >>> with open("path/to/my/file.ext", "rb") as f: data = f.read()
            >>> response = api_client.upload_annotation(annotation_id=1, annotation_data=data)

        Args:
            annotation_id: ID of the associated annotation entry
            annotation_data: byte data

        Returns:
            HTTP response containing the updated annotation
        """

        return requests.post(
            self.routes["upload-annotation"].format(annotation_id=annotation_id),
            headers=self.headers,
            files={"file": io.BytesIO(annotation_data)},
        )

    def get_annotation_url(self, annotation_id: int) -> Response:
        """Get the image as a URL

        Example::
            >>> from pyrostorage import client
            >>> api_client = client.Client("http://pyro-storage.herokuapp.com", "MY_LOGIN", "MY_PWD")
            >>> response = api_client.get_annotation_url(1)

        Args:
            annotation_id: the identifier of the annotation entry

        Returns:
            HTTP response containing the URL to the annotation content
        """

        return requests.get(self.routes["get-annotation-url"].format(annotation_id=annotation_id), headers=self.headers)
