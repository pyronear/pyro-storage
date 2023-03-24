# Copyright (C) 2022-2023, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

from app import config as cfg
from app.services.bucket import QarnotBucket

__all__ = ["media_bucket", "annotations_bucket"]


media_bucket = QarnotBucket(cfg.BUCKET_NAME, cfg.BUCKET_MEDIA_FOLDER)
annotations_bucket = QarnotBucket(cfg.BUCKET_NAME, cfg.BUCKET_ANNOT_FOLDER)
