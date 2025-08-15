import time
from collections.abc import Iterator
from pathlib import Path

import requests
from loguru import logger

from ..config import ImgurConfig
from .base import SUPPORTED_IMAGE_EXTENSIONS, BaseProvider, ImageInfo


class ImgurProvider(BaseProvider):
    """Imgur Provider"""

    def __init__(self, config: ImgurConfig):
        super().__init__(config)
        self.config: ImgurConfig = config
        self.logger = logger
        self.api_base = "https://api.imgur.com/3"

    def test_connection(self) -> bool:
        """Test Imgur connection

        Returns
        -------
        bool
            True if connection is successful, False otherwise.
        """
        try:
            headers = {"Authorization": f"Bearer {self.config.access_token}"}
            response = requests.get(
                f"{self.api_base}/account/me", headers=headers, timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Imgur connection test failed: {e}")
            return False

    def list_images(self, limit: int | None = None) -> Iterator[ImageInfo]:
        """List all images in Imgur

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
            headers = {"Authorization": f"Bearer {self.config.access_token}"}
            count = 0
            page = 0

            while True:
                if limit and count >= limit:
                    break

                # Get user's images
                response = requests.get(
                    f"{self.api_base}/account/me/images/{page}",
                    headers=headers,
                    timeout=30,
                )

                if response.status_code != 200:
                    self.logger.error(
                        f"Failed to get Imgur image list: {response.status_code}"
                    )
                    break

                data = response.json()

                if not data.get("success") or not data.get("data"):
                    self.logger.warning(
                        "Imgur API returned no data or unsuccessful response"
                    )
                    break

                images = data["data"]
                if not images:
                    break

                for img in images:
                    if limit and count >= limit:
                        break

                    # Validate image data
                    if not img or not isinstance(img, dict):
                        continue

                    # Get URL - required field
                    url = img.get("link")
                    if not url:
                        continue

                    # Get filename (from title or extract from link)
                    filename = img.get("title") or Path(url).name
                    if not any(
                        filename.lower().endswith(ext)
                        for ext in SUPPORTED_IMAGE_EXTENSIONS
                    ):
                        # Try to get file extension from URL
                        url_filename = Path(url).name
                        if any(
                            url_filename.lower().endswith(ext)
                            for ext in SUPPORTED_IMAGE_EXTENSIONS
                        ):
                            filename = url_filename
                        else:
                            # Default to jpg if we can't determine extension
                            filename += ".jpg"

                    yield ImageInfo(
                        url=url,
                        filename=filename,
                        size=img.get("size"),
                        created_at=img.get("datetime"),
                        metadata={
                            "id": img.get("id"),
                            "title": img.get("title"),
                            "description": img.get("description"),
                            "type": img.get("type"),
                            "width": img.get("width"),
                            "height": img.get("height"),
                            "views": img.get("views"),
                            "deletehash": img.get("deletehash"),
                        },
                    )
                    count += 1

                # If the number of returned images is 0, there are no more images
                if len(images) == 0:
                    break

                page += 1

                # Add delay to avoid frequent requests
                time.sleep(0.1)

        except Exception as e:
            self.logger.error(f"Failed to list Imgur images: {e}")
            raise

    def download_image(self, image_info: ImageInfo, output_path: Path) -> bool:
        """Download image from Imgur

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
        """Get the total number of images in Imgur

        Returns
        -------
        int or None
            The total number of images, or None if unable to determine.
        """
        try:
            headers = {"Authorization": f"Bearer {self.config.access_token}"}
            response = requests.get(
                f"{self.api_base}/account/me", headers=headers, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    account_data = data.get("data", {})
                    return account_data.get("total_images", 0)

            return None
        except Exception as e:
            self.logger.warning(f"Failed to get the total number of Imgur images: {e}")
            return None
