import io
import logging
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from app.config import settings

logger = logging.getLogger("ragmate.storage")


class BaseStorageProvider(ABC):
    """Abstract interface for document file storage in DocuRAG."""

    @abstractmethod
    def save_file(self, content: bytes, destination_filename: str) -> str:
        """
        Saves raw document bytes and returns the persistent identifier or storage path.
        """
        pass

    @abstractmethod
    def get_file(self, identifier: str) -> bytes:
        """
        Retrieves raw byte contents of the document.
        """
        pass

    @abstractmethod
    def get_local_path(self, identifier: str) -> str:
        """
        Ensures a readable local file path exists on disk for PyMuPDF page extraction.
        For cloud storage, this downloads to a local cache directory if not already cached.
        """
        pass

    @abstractmethod
    def delete_file(self, identifier: str) -> bool:
        """
        Deletes the file from persistent storage.
        """
        pass

    @abstractmethod
    def file_exists(self, identifier: str) -> bool:
        """
        Verifies whether the file exists in persistent storage.
        """
        pass


class LocalStorageProvider(BaseStorageProvider):
    """
    Local filesystem storage provider with path traversal defenses.
    Ideal for local development, Docker persistent volumes, or cloud instances with mounted disks.
    """

    def __init__(self, upload_dir: Optional[str] = None):
        self.upload_dir = Path(upload_dir or settings.UPLOAD_DIRECTORY).resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, identifier: str) -> Path:
        # If identifier is an absolute path or relative filename
        path = Path(identifier)
        if not path.is_absolute():
            path = (self.upload_dir / path).resolve()
        else:
            path = path.resolve()

        # Enforce that the path stays within the designated upload directory
        if not str(path).startswith(str(self.upload_dir)):
            raise ValueError("Path traversal detected: storage path outside root upload directory.")
        return path

    def save_file(self, content: bytes, destination_filename: str) -> str:
        target_path = self._resolve_safe_path(destination_filename)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(content)
        logger.info("Saved %d bytes to local storage at: %s", len(content), target_path)
        return str(target_path)

    def get_file(self, identifier: str) -> bytes:
        target_path = self._resolve_safe_path(identifier)
        if not target_path.exists():
            raise FileNotFoundError(f"Document file not found at: {target_path}")
        with open(target_path, "rb") as f:
            return f.read()

    def get_local_path(self, identifier: str) -> str:
        target_path = self._resolve_safe_path(identifier)
        if not target_path.exists():
            raise FileNotFoundError(f"Document file not found at: {target_path}")
        return str(target_path)

    def delete_file(self, identifier: str) -> bool:
        try:
            target_path = self._resolve_safe_path(identifier)
            if target_path.exists():
                target_path.unlink()
                logger.info("Deleted local file: %s", target_path)
                return True
        except Exception as e:
            logger.warning("Error deleting file '%s': %s", identifier, e)
        return False

    def file_exists(self, identifier: str) -> bool:
        try:
            target_path = self._resolve_safe_path(identifier)
            return target_path.exists()
        except Exception:
            return False


class S3StorageProvider(BaseStorageProvider):
    """
    S3-compatible Object Storage provider.
    Works with AWS S3, Cloudflare R2, Supabase Storage S3 API, MinIO, and Backblaze B2.
    """

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        region_name: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        cache_dir: Optional[str] = None,
    ):
        import boto3
        from botocore.config import Config

        self.bucket_name = bucket_name or settings.STORAGE_BUCKET or "ragmate-documents"
        self.endpoint_url = endpoint_url or settings.STORAGE_ENDPOINT_URL
        self.region_name = region_name or settings.STORAGE_REGION or "us-east-1"
        self.access_key = access_key or settings.STORAGE_ACCESS_KEY
        self.secret_key = secret_key or settings.STORAGE_SECRET_KEY

        # Local cache for PyMuPDF page-level extraction
        self.cache_dir = Path(cache_dir or os.path.join(settings.UPLOAD_DIRECTORY, "s3_cache")).resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        client_kwargs = {
            "service_name": "s3",
            "region_name": self.region_name,
            "config": Config(signature_version="s3v4"),
        }
        if self.endpoint_url:
            client_kwargs["endpoint_url"] = self.endpoint_url
        if self.access_key and self.secret_key:
            client_kwargs["aws_access_key_id"] = self.access_key
            client_kwargs["aws_secret_access_key"] = self.secret_key

        self.s3_client = boto3.client(**client_kwargs)
        logger.info(
            "Initialized S3StorageProvider (bucket='%s', region='%s', endpoint='%s')",
            self.bucket_name,
            self.region_name,
            self.endpoint_url or "AWS Default",
        )

    def _normalize_key(self, identifier: str) -> str:
        # Strip any local directory prefixes to obtain the object key
        return Path(identifier).name

    def save_file(self, content: bytes, destination_filename: str) -> str:
        key = self._normalize_key(destination_filename)
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content,
            ContentType="application/pdf",
        )
        logger.info("Uploaded %d bytes to S3: s3://%s/%s", len(content), self.bucket_name, key)

        # Also write to local cache so immediate processing doesn't need re-download
        cached_path = self.cache_dir / key
        with open(cached_path, "wb") as f:
            f.write(content)

        return f"s3://{self.bucket_name}/{key}"

    def get_file(self, identifier: str) -> bytes:
        key = self._normalize_key(identifier)
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
        return response["Body"].read()

    def get_local_path(self, identifier: str) -> str:
        key = self._normalize_key(identifier)
        cached_path = self.cache_dir / key

        if not cached_path.exists():
            logger.info("Downloading s3://%s/%s to local cache: %s", self.bucket_name, key, cached_path)
            content = self.get_file(identifier)
            with open(cached_path, "wb") as f:
                f.write(content)

        return str(cached_path)

    def delete_file(self, identifier: str) -> bool:
        key = self._normalize_key(identifier)
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info("Deleted object from S3: s3://%s/%s", self.bucket_name, key)
            cached_path = self.cache_dir / key
            if cached_path.exists():
                cached_path.unlink()
            return True
        except Exception as e:
            logger.warning("Error deleting object s3://%s/%s: %s", self.bucket_name, key, e)
            return False

    def file_exists(self, identifier: str) -> bool:
        from botocore.exceptions import ClientError
        key = self._normalize_key(identifier)
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                return False
            logger.warning("S3 head_object error on key '%s': %s", key, e)
            return False


_storage_singleton: Optional[BaseStorageProvider] = None


def get_storage_provider() -> BaseStorageProvider:
    """Returns the configured storage provider singleton."""
    global _storage_singleton
    if _storage_singleton is None:
        provider_type = getattr(settings, "STORAGE_PROVIDER", "local").lower()
        if provider_type in ("s3", "r2", "supabase") and settings.STORAGE_BUCKET:
            try:
                _storage_singleton = S3StorageProvider()
            except Exception as e:
                logger.error("Failed to initialize S3 storage provider: %s. Falling back to LocalStorage.", e)
                _storage_singleton = LocalStorageProvider()
        else:
            _storage_singleton = LocalStorageProvider()
    return _storage_singleton
