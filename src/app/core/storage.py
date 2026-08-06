import boto3
from botocore.client import Config

from app.config import settings

# Build ONE S3 client for the app, pointed at MinIO. Because MinIO is
# S3-compatible, this exact code works against real AWS S3 by only changing
# the endpoint/keys in config — no code change.
_s3_client = boto3.client(
    "s3",
    endpoint_url=settings.minio_endpoint,          # <-- point at MinIO, not AWS
    aws_access_key_id=settings.minio_access_key,
    aws_secret_access_key=settings.minio_secret_key,
    config=Config(signature_version="s3v4"),        # the auth scheme MinIO expects
)


def ensure_bucket_exists() -> None:
    # Buckets must exist before you put objects in them. On startup we check for
    # our bucket and create it if missing, so a fresh MinIO "just works".
    existing = _s3_client.list_buckets().get("Buckets", [])
    names = {b["Name"] for b in existing}
    if settings.minio_bucket not in names:
        _s3_client.create_bucket(Bucket=settings.minio_bucket)


def upload_fileobj(fileobj, object_key: str, content_type: str) -> None:
    # Stream the file's bytes into MinIO under object_key. "fileobj" is a
    # file-like object (the uploaded file's stream) — boto3 reads from it
    # directly, so we don't have to load the whole file into memory at once.
    _s3_client.upload_fileobj(
        fileobj,
        settings.minio_bucket,
        object_key,
        ExtraArgs={"ContentType": content_type},
    )


def download_fileobj(object_key: str):
    # Fetch an object's bytes back out. get_object returns a streaming body
    # under the "Body" key. We'll use this in a later sub-step when processing.
    response = _s3_client.get_object(Bucket=settings.minio_bucket, Key=object_key)
    return response["Body"]