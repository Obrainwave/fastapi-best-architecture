# app/storage/s3.py
import boto3
import aioboto3
from botocore.config import Config

from app.core.config import settings
from app.storage.base import StorageBackend, UploadResult


class S3StorageBackend(StorageBackend):
    def __init__(self) -> None:
        self.bucket = settings.S3_BUCKET
        self.session = aioboto3.Session()
        self._client_kwargs = dict(
            region_name=settings.S3_REGION,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            endpoint_url=settings.S3_ENDPOINT_URL,
            config=Config(signature_version="s3v4"),
        )

    async def save(self, key: str, data: bytes, content_type: str | None = None) -> UploadResult:
        async with self.session.client("s3", **self._client_kwargs) as s3:
            await s3.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type or "application/octet-stream")
        return UploadResult(key=key, url=f"s3://{self.bucket}/{key}")

    async def save_file(self, key: str, local_path: str, content_type: str | None = None) -> UploadResult:
        async with self.session.client("s3", **self._client_kwargs) as s3:
            extra_args = {"ContentType": content_type} if content_type else {}
            await s3.upload_file(local_path, self.bucket, key, ExtraArgs=extra_args)
        return UploadResult(key=key, url=f"s3://{self.bucket}/{key}")

    async def read(self, key: str) -> bytes:
        async with self.session.client("s3", **self._client_kwargs) as s3:
            response = await s3.get_object(Bucket=self.bucket, Key=key)
            async with response["Body"] as stream:
                return await stream.read()

    async def delete(self, key: str) -> None:
        async with self.session.client("s3", **self._client_kwargs) as s3:
            await s3.delete_object(Bucket=self.bucket, Key=key)

    def signed_url(self, key: str, ttl_seconds: int) -> str:
        client = boto3.client(
            "s3",
            region_name=settings.S3_REGION,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            endpoint_url=settings.S3_ENDPOINT_URL,
            config=Config(signature_version="s3v4"),
        )
        return client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=ttl_seconds,
        )