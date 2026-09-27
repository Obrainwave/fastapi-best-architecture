# app/storage/factory.py
from functools import lru_cache

from app.core.config import settings
from app.storage.base import StorageBackend
from app.storage.local import LocalStorageBackend
from app.storage.s3 import S3StorageBackend


@lru_cache
def get_storage() -> StorageBackend:
    return S3StorageBackend() if settings.STORAGE_BACKEND == "s3" else LocalStorageBackend()