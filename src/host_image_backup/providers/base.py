from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

# Supported image file extensions
SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    ".svg",
    ".tiff",
    ".tif",
    ".ico",
}


@dataclass
class ImageInfo:
    """Image information

    Parameters
    ----------
    url : str
        The URL of the image.
    filename : str
        The filename of the image.
    size : int, optional
        The size of the image in bytes.
    created_at : str, optional
        The creation timestamp of the image.
    tags : list of str, optional
        Tags associated with the image.
    metadata : dict, optional
        Additional metadata about the image.
    """

    url: str
    filename: str
    size: int | None = None
    created_at: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class FileInfo:
    """File information for local files

    Parameters
    ----------
    path : str
        The file path.
    filename : str
        The filename.
    size : int
        The file size in bytes.
    hash : str
        The file hash (MD5/SHA256).
    modified_time : datetime
        The last modified time.
    created_time : datetime
        The creation time.
    """

    path: str
    filename: str
    size: int
    hash: str
    modified_time: datetime
    created_time: datetime


@dataclass
class SingleUploadResult:
    """Single file upload result information

    Parameters
    ----------
    success : bool
        Whether the upload was successful.
    url : str, optional
        The URL of the uploaded image.
    message : str, optional
        Success or error message.
    metadata : dict, optional
        Additional metadata about the upload.
    """

    success: bool
    url: str | None = None
    message: str | None = None
    metadata: dict[str, Any] | None = None


class BaseProvider(ABC):
    """Base class for image hosting providers

    This is the base class that all provider implementations should inherit from.
    """

    def __init__(self, config: Any):
        """Initialize provider

        Parameters
        ----------
        config : Any
            The provider configuration object.
        """
        self.config = config
        self.logger = logger

    @abstractmethod
    def test_connection(self) -> bool:
        """Test if connection is working

        Returns
        -------
        bool
            True if connection is successful, False otherwise.
        """
        pass

    @abstractmethod
    def list_images(self, limit: int | None = None) -> Iterator[ImageInfo]:
        """List all images

        Parameters
        ----------
        limit : int, optional
            Limit the number of images returned. If None, no limit is applied.

        Yields
        ------
        ImageInfo
            Information about each image.
        """
        pass

    @abstractmethod
    def download_image(self, image_info: ImageInfo, output_path: Path) -> bool:
        """Download image to local storage

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
        pass

    @abstractmethod
    def upload_image(
        self, file_path: Path, remote_path: str | None = None
    ) -> SingleUploadResult:
        """Upload image to the provider

        Parameters
        ----------
        file_path : Path
            The local file path to upload.
        remote_path : str, optional
            The remote path where the image should be saved.
            If None, use the original filename.

        Returns
        -------
        UploadResult
            The upload result containing success status and metadata.
        """
        pass

    def get_file_info(self, remote_path: str) -> FileInfo | None:
        """Get file information from remote storage

        Parameters
        ----------
        remote_path : str
            The remote file path.

        Returns
        -------
        FileInfo or None
            The file information, or None if not found.
        """
        # Default implementation: not supported by all providers
        self.logger.warning(
            f"get_file_info not implemented for {self.get_provider_name()}"
        )
        return None

    def delete_image(self, remote_path: str) -> bool:
        """Delete image from remote storage

        Parameters
        ----------
        remote_path : str
            The remote file path to delete.

        Returns
        -------
        bool
            True if deletion was successful, False otherwise.
        """
        # Default implementation: not supported by all providers
        self.logger.warning(
            f"delete_image not implemented for {self.get_provider_name()}"
        )
        return False

    def get_image_count(self) -> int | None:
        """Get total number of images

        Returns
        -------
        int or None
            The total number of images, or None if unable to determine.
        """
        # Default implementation: iterate through all images and count (may be slow)
        try:
            count = 0
            for _ in self.list_images():
                count += 1
            return count
        except Exception as e:
            self.logger.warning(f"Unable to get image count: {e}")
            return None

    def validate_config(self) -> bool:
        """Validate if configuration is valid

        Returns
        -------
        bool
            True if configuration is valid, False otherwise.
        """
        return self.config.validate_config()

    def get_provider_name(self) -> str:
        """Get provider name

        Returns
        -------
        str
            The name of the provider.
        """
        return self.config.name

    def is_enabled(self) -> bool:
        """Check if provider is enabled

        Returns
        -------
        bool
            True if provider is enabled, False otherwise.
        """
        return self.config.enabled
