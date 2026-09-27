# app/storage/base.py
import abc
from dataclasses import dataclass


@dataclass
class UploadResult:
    key: str
    url: str


class StorageBackend(abc.ABC):
    @abc.abstractmethod
    async def save(self, key: str, data: bytes, content_type: str | None = None) -> UploadResult: ...

    @abc.abstractmethod
    async def save_file(self, key: str, local_path: str, content_type: str | None = None) -> UploadResult: ...

    @abc.abstractmethod
    async def read(self, key: str) -> bytes: ...

    @abc.abstractmethod
    async def delete(self, key: str) -> None: ...

    @abc.abstractmethod
    def signed_url(self, key: str, ttl_seconds: int) -> str: ...