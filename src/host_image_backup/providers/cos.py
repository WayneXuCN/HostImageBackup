from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

import requests
from loguru import logger
from qcloud_cos import CosConfig, CosS3Client

from ..config import COSConfig
from .base import (
    SUPPORTED_IMAGE_EXTENSIONS,
    BaseProvider,
    FileInfo,
    ImageInfo,
    SingleUploadResult,
)


class COSProvider(BaseProvider):
    """Tencent Cloud COS Provider"""

    def __init__(self, config: COSConfig):
        super().__init__(config)
        self.config: COSConfig = config
        self.logger = logger
        self._client = None

    @property
    def client(self) -> CosS3Client:
        """Get COS client

        Returns
        -------
        CosS3Client
            The COS client instance.
        """
        if self._client is None:
            cos_config = CosConfig(
                Region=self.config.region,
                SecretId=self.config.secret_id,
                SecretKey=self.config.secret_key,
            )
            self._client = CosS3Client(cos_config)
        return self._client

    def test_connection(self) -> bool:
        """Test COS connection

        Returns
        -------
        bool
            True if connection is successful, False otherwise.
        """
        try:
            # Attempt to get bucket information
            response = self.client.head_bucket(Bucket=self.config.bucket)
            return response["ResponseMetadata"]["HTTPStatusCode"] == 200
        except Exception as e:
            self.logger.error(f"COS connection test failed: {e}")
            return False

    def list_images(self, limit: int | None = None) -> Iterator[ImageInfo]:
        """List all images in COS

        Parameters
        ----------
        limit : int, optional
            Limit the number of images returned. If None, no limit is applied.

        Yields
        ------
        ImageInfo
            Information about each image.
        """
        try:
            count = 0
            marker = ""
            image_extensions = SUPPORTED_IMAGE_EXTENSIONS

            while True:
                if limit and count >= limit:
                    break

                # Get object list
                response = self.client.list_objects(
                    Bucket=self.config.bucket,
                    Prefix=self.config.prefix,
                    Marker=marker,
                    MaxKeys=1000,
                )

                if "Contents" not in response:
                    break

                for obj in response["Contents"]:
                    if limit and count >= limit:
                        break

                    key = obj["Key"]
                    file_ext = Path(key).suffix.lower()

                    if file_ext not in image_extensions:
                        continue

                    # Construct image URL
                    url = f"https://{self.config.bucket}.cos.{self.config.region}.myqcloud.com/{key}"

                    yield ImageInfo(
                        url=url,
                        filename=Path(key).name,
                        size=obj.get("Size"),
                        created_at=obj.get("LastModified"),
                        metadata={
                            "key": key,
                            "etag": obj.get("ETag", "").strip('"'),
                            "storage_class": obj.get("StorageClass"),
                        },
                    )
                    count += 1

                # Check if there are more objects
                # Fix the pagination logic - IsTruncated can be a boolean or string
                is_truncated = response.get("IsTruncated")
                if not is_truncated or is_truncated in (False, "false", "False"):
                    break

                marker = response.get("NextMarker", "")
                if not marker and response.get("Contents"):
                    marker = response["Contents"][-1]["Key"]

        except Exception as e:
            self.logger.error(f"Failed to list COS images: {e}")
            raise

    def download_image(self, image_info: ImageInfo, output_path: Path) -> bool:
        """Download image from COS

        Parameters
        ----------
        image_info : ImageInfo
            Information about the image to download.
        output_path : Path
            The path where the image should be saved.

        Returns
        -------
        bool
            True if download is successful, False otherwise.
        """
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Get key from metadata
            key = image_info.metadata.get("key") if image_info.metadata else None

            if key:
                # Download directly from COS
                response = self.client.get_object(Bucket=self.config.bucket, Key=key)

                with open(output_path, "wb") as f:
                    for chunk in response["Body"].iter_chunks():
                        f.write(chunk)
            else:
                # Download via URL
                response = requests.get(image_info.url, timeout=30, stream=True)
                response.raise_for_status()

                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

            self.logger.debug(f"Successfully downloaded image: {image_info.filename}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to download image {image_info.filename}: {e}")
            return False

    def get_image_count(self) -> int | None:
        """Get total number of images in COS

        Returns
        -------
        int or None
            The total number of images, or None if unable to determine.
        """
        try:
            count = 0
            marker = ""
            image_extensions = SUPPORTED_IMAGE_EXTENSIONS

            while True:
                response = self.client.list_objects(
                    Bucket=self.config.bucket,
                    Prefix=self.config.prefix,
                    Marker=marker,
                    MaxKeys=1000,
                )

                if "Contents" not in response:
                    break

                for obj in response["Contents"]:
                    key = obj["Key"]
                    file_ext = Path(key).suffix.lower()
                    if file_ext in image_extensions:
                        count += 1

                # Fix the pagination logic - IsTruncated can be a boolean or string
                is_truncated = response.get("IsTruncated")
                if not is_truncated or is_truncated in (False, "false", "False"):
                    break

                marker = response.get("NextMarker", "")
                if not marker and response.get("Contents"):
                    marker = response["Contents"][-1]["Key"]

            return count
        except Exception as e:
            self.logger.warning(f"Failed to get total number of COS images: {e}")
            return None

    def upload_image(
        self, file_path: Path, remote_path: str | None = None
    ) -> SingleUploadResult:
        """Upload image to COS

        Parameters
        ----------
        file_path : Path
            The local file path to upload.
        remote_path : str, optional
            The remote path where the image should be saved.
            If None, use the original filename.

        Returns
        -------
        SingleUploadResult
            The upload result containing success status and metadata.
        """
        try:
            # Determine remote path
            if remote_path is None:
                remote_path = self.config.prefix + file_path.name
            elif self.config.prefix and not remote_path.startswith(self.config.prefix):
                remote_path = self.config.prefix + remote_path

            # Check if file exists
            if not file_path.exists():
                return SingleUploadResult(
                    success=False, message=f"File not found: {file_path}"
                )

            # Upload file
            with open(file_path, "rb") as f:
                response = self.client.put_object(
                    Bucket=self.config.bucket, Key=remote_path, Body=f
                )

            # Generate URL
            url = f"https://{self.config.bucket}.cos.{self.config.region}.myqcloud.com/{remote_path}"

            return SingleUploadResult(
                success=True,
                url=url,
                message=f"Successfully uploaded {file_path.name} to {remote_path}",
                metadata={
                    "key": remote_path,
                    "etag": response.get("ETag", "").strip('"'),
                    "size": file_path.stat().st_size,
                    "last_modified": datetime.now().isoformat(),
                },
            )

        except Exception as e:
            self.logger.error(f"Failed to upload image {file_path}: {e}")
            return SingleUploadResult(success=False, message=f"Upload failed: {str(e)}")

    def get_file_info(self, remote_path: str) -> FileInfo | None:
        """Get file information from COS

        Parameters
        ----------
        remote_path : str
            The remote file path.

        Returns
        -------
        FileInfo or None
            The file information, or None if not found.
        """
        try:
            # Get object metadata
            response = self.client.head_object(
                Bucket=self.config.bucket, Key=remote_path
            )

            # Parse last modified time
            last_modified = None
            last_modified_str = response.get("LastModified")
            if last_modified_str:
                try:
                    # COS returns ISO format string
                    last_modified = datetime.fromisoformat(
                        last_modified_str.replace("Z", "+00:00")
                    )
                except ValueError:
                    last_modified = datetime.now()

            return FileInfo(
                path=remote_path,
                filename=Path(remote_path).name,
                size=response.get("ContentLength", 0),
                hash=response.get("ETag", "").strip('"'),
                modified_time=last_modified or datetime.now(),
                created_time=last_modified or datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Failed to get file info for {remote_path}: {e}")
            return None

    def delete_image(self, remote_path: str) -> bool:
        """Delete image from COS

        Parameters
        ----------
        remote_path : str
            The remote file path to delete.

        Returns
        -------
        bool
            True if deletion was successful, False otherwise.
        """
        try:
            response = self.client.delete_object(
                Bucket=self.config.bucket, Key=remote_path
            )
            return response["ResponseMetadata"]["HTTPStatusCode"] == 204
        except Exception as e:
            self.logger.error(f"Failed to delete image {remote_path}: {e}")
            return False
