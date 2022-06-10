# Copyright (C) 2021, Pyronear contributors.

# This program is licensed under the Apache License version 2.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0.txt> for full license details.

from app.services import annotations_bucket, media_bucket, resolve_bucket_key
from app.services.bucket import QarnotBucket


def test_resolve_bucket_key(monkeypatch):
    file_name = "myfile.jpg"
    bucket_subfolder = "my/bucket/subfolder"

    # Same if the bucket folder is specified
    assert resolve_bucket_key(file_name, bucket_subfolder) == f"{bucket_subfolder}/{file_name}"

    # Check that it returns the same thing when bucket folder is not set
    assert resolve_bucket_key(file_name) == file_name


def test_bucket_service():
    assert isinstance(media_bucket, QarnotBucket)
    assert isinstance(annotations_bucket, QarnotBucket)
