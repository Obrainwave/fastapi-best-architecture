# app/storage/local.py
import os
import shutil

from app.core.config import settings
from app.storage.base import StorageBackend, UploadResult


class LocalStorageBackend(StorageBackend):
    def __init__(self) -> None:
        self.root = settings.LOCAL_STORAGE_ROOT
        os.makedirs(self.root, exist_ok=True)

    def _path(self, key: str) -> str:
        path = os.path.join(self.root, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    async def save(self, key: str, data: bytes, content_type: str | None = None) -> UploadResult:
        with open(self._path(key), "wb") as f:
            f.write(data)
        return UploadResult(key=key, url=f"{settings.LOCAL_STORAGE_BASE_URL}/{key}")

    async def save_file(self, key: str, local_path: str, content_type: str | None = None) -> UploadResult:
        shutil.copyfile(local_path, self._path(key))
        return UploadResult(key=key, url=f"{settings.LOCAL_STORAGE_BASE_URL}/{key}")

    async def read(self, key: str) -> bytes:
        with open(self._path(key), "rb") as f:
            return f.read()

    async def delete(self, key: str) -> None:
        path = self._path(key)
        if os.path.exists(path):
            os.remove(path)

    def signed_url(self, key: str, ttl_seconds: int) -> str:
        # No CDN in front of local storage, playback goes through the
        # authenticated segment passthrough route instead of this URL directly.
        return f"{settings.LOCAL_STORAGE_BASE_URL}/{key}"