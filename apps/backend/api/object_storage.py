"""S3-compatible object storage client for scan images."""

from config import settings


class S3CompatibleMediaStorage:
    """MinIO/AWS S3 compatible media storage."""

    backend = "s3-compatible"

    def __init__(self) -> None:
        import boto3
        from botocore.client import Config

        self.bucket = settings.s3_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url or None,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            config=Config(s3={"addressing_style": "path" if settings.s3_force_path_style else "auto"}),
        )

    def put_object(self, *, object_key: str, content: bytes, content_type: str) -> str:
        self.client.put_object(
            Bucket=self.bucket,
            Key=object_key,
            Body=content,
            ContentType=content_type,
        )
        return object_key

    def presigned_get_url(self, *, object_key: str, expires_seconds: int = 900) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": object_key},
            ExpiresIn=expires_seconds,
        )


class LazyMediaStorage:
    backend = "s3-compatible"

    def __init__(self) -> None:
        self._client: S3CompatibleMediaStorage | None = None

    def _get(self) -> S3CompatibleMediaStorage:
        if self._client is None:
            self._client = S3CompatibleMediaStorage()
        return self._client

    def put_object(self, *, object_key: str, content: bytes, content_type: str) -> str:
        return self._get().put_object(object_key=object_key, content=content, content_type=content_type)

    def presigned_get_url(self, *, object_key: str, expires_seconds: int = 900) -> str:
        return self._get().presigned_get_url(object_key=object_key, expires_seconds=expires_seconds)


media_storage_client = LazyMediaStorage()
