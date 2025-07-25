import time
from collections.abc import Iterator
from pathlib import Path

import requests
from loguru import logger

from ..config import SMSConfig
from .base import BaseProvider, ImageInfo


class SMSProvider(BaseProvider):
    """SM.MS Provider"""

    def __init__(self, config: SMSConfig):
        super().__init__(config)
        self.config: SMSConfig = config
        self.logger = logger
        self.api_base = "https://sm.ms/api/v2"

    def test_connection(self) -> bool:
        """Test SM.MS connection

        Returns
        -------
        bool
            True if connection is successful, False otherwise.
        """
        try:
            headers = {"Authorization": self.config.api_token}
            response = requests.get(
                f"{self.api_base}/profile", headers=headers, timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"SM.MS connection test failed: {e}")
            return False

    def list_images(self, limit: int | None = None) -> Iterator[ImageInfo]:
        """List all images in SM.MS

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
            headers = {"Authorization": self.config.api_token}
            count = 0
            page = 1

            while True:
                if limit and count >= limit:
                    break

                # Get user's images
                response = requests.get(
                    f"{self.api_base}/upload_history",
                    headers=headers,
                    params={"page": page},
                    timeout=30,
                )

                if response.status_code != 200:
                    self.logger.error(
                        f"Failed to get SM.MS image list: {response.status_code}"
                    )
                    break

                data = response.json()

                if not data.get("success") or not data.get("data"):
                    self.logger.warning(
                        "SM.MS API returned no data or unsuccessful response"
                    )
                    break

                images = data["data"].get("data", [])
                if not images:
                    break

                for img in images:
                    if limit and count >= limit:
                        break

                    # Validate image data
                    if not img or not isinstance(img, dict):
                        continue

                    # Get URL - required field
                    url = img.get("url")
                    if not url:
                        continue

                    # Get filename (from storename or extract from link)
                    filename = img.get("storename") or Path(url).name

                    yield ImageInfo(
                        url=url,
                        filename=filename,
                        size=img.get("size"),
                        created_at=img.get("created_at"),  # Already in ISO format
                        metadata={
                            "hash": img.get("hash"),
                            "delete": img.get("delete"),
                            "page": img.get("page"),
                            "path": img.get("path"),
                            "width": img.get("width"),
                            "height": img.get("height"),
                        },
                    )
                    count += 1

                # Check if there are more pages
                current_page = data["data"].get("current_page", 1)
                total_pages = data["data"].get("total_page", 1)

                if current_page >= total_pages:
                    break

                page += 1

                # Add delay to avoid frequent requests
                time.sleep(0.1)

        except Exception as e:
            self.logger.error(f"Failed to list SM.MS images: {e}")
            raise

    def download_image(self, image_info: ImageInfo, output_path: Path) -> bool:
        """Download image from SM.MS

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
            # Ensure the output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

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
        """Get the total number of images in SM.MS

        Returns
        -------
        int or None
            The total number of images, or None if unable to determine.
        """
        try:
            headers = {"Authorization": self.config.api_token}
            response = requests.get(
                f"{self.api_base}/profile", headers=headers, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    profile_data = data.get("data", {})
                    return profile_data.get("disk_usage", {}).get("image_count", 0)

            return None
        except Exception as e:
            self.logger.warning(f"Failed to get the total number of SM.MS images: {e}")
            return None
