from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
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
