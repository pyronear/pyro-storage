from app.services import resolve_bucket_key, s3_bucket
from app.services.bucket import S3Bucket


def test_resolve_bucket_key(monkeypatch):
    file_name = "myfile.jpg"
    bucket_subfolder = "my/bucket/subfolder"

    # Same if the bucket folder is specified
    assert resolve_bucket_key(file_name, bucket_subfolder) == f"{bucket_subfolder}/{file_name}"

    # Check that it returns the same thing when bucket folder is not set
    assert resolve_bucket_key(file_name) == file_name


def test_bucket_service():
    assert isinstance(s3_bucket, S3Bucket)
