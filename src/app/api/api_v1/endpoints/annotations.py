# Copyright (C) 2022-2024, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Path, Security, UploadFile, status

from app.schemas.annotations import  AnnotationCreate, AnnotationIn, AnnotationOut, AnnotationUrl

router = APIRouter()
