from collections.abc import Iterator
from pathlib import Path

import requests
from loguru import logger

from ..config import GitHubConfig
from .base import SUPPORTED_IMAGE_EXTENSIONS, BaseProvider, ImageInfo


class GitHubProvider(BaseProvider):
    """GitHub Provider"""

    def __init__(self, config: GitHubConfig):
        super().__init__(config)
        self.config: GitHubConfig = config
        self.logger = logger
        self.api_base = "https://api.github.com"

    def test_connection(self) -> bool:
        """Test GitHub connection

        Returns
        -------
        bool
            True if connection is successful, False otherwise.
        """
        try:
            headers = {
                "Authorization": f"token {self.config.token}",
                "Accept": "application/vnd.github.v3+json",
            }
            response = requests.get(
                f"{self.api_base}/repos/{self.config.owner}/{self.config.repo}",
                headers=headers,
                timeout=10,
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"GitHub connection test failed: {e}")
            return False

    def list_images(self, limit: int | None = None) -> Iterator[ImageInfo]:
        """List all images in GitHub repository

        Parameters
        ----------
        limit : int, optional
            Limit the number of images returned. If None, no limit is applied.

        Yields
        ------
        ImageInfo
            Information about each image.
        """
        headers = {
            "Authorization": f"token {self.config.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        count = 0
        image_extensions = SUPPORTED_IMAGE_EXTENSIONS

        # Use iterative approach instead of recursion to avoid potential stack overflow
        paths_to_process = [self.config.path.rstrip("/") if self.config.path else ""]
        processed_paths = set()

        while paths_to_process and (limit is None or count < limit):
            path = paths_to_process.pop(0)

            # Avoid processing the same path multiple times
            if path in processed_paths:
                continue
            processed_paths.add(path)

            url = (
                f"{self.api_base}/repos/{self.config.owner}/{self.config.repo}/contents"
            )
            if path:
                url += f"/{path}"

            try:
                response = requests.get(url, headers=headers, timeout=30)

                if response.status_code != 200:
                    self.logger.warning(
                        f"Unable to get GitHub directory contents: {path}, Status code: {response.status_code}"
                    )
                    continue

                contents = response.json()

                for item in contents:
                    if limit is not None and count >= limit:
                        break

                    if item["type"] == "file":
                        file_path = item["path"]
                        file_ext = Path(file_path).suffix.lower()

                        # Check if path matches configured path prefix
                        if self.config.path and not file_path.startswith(
                            self.config.path
                        ):
                            continue

                        if file_ext in image_extensions:
                            # Construct image URL
                            url = item["download_url"]

                            yield ImageInfo(
                                url=url,
                                filename=Path(file_path).name,
                                size=item.get("size"),
                                created_at=None,  # GitHub API doesn't provide creation time
                                metadata={"sha": item.get("sha"), "path": file_path},
                            )
                            count += 1

                    elif item["type"] == "dir":
                        # Add subdirectory to processing queue
                        paths_to_process.append(item["path"])

            except Exception as e:
                self.logger.error(f"Error listing GitHub files: {e}")

    def download_image(self, image_info: ImageInfo, output_path: Path) -> bool:
        """Download image from GitHub

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

            # Get download URL from metadata or construct it
            url = image_info.url

            # Download the image
            response = requests.get(url, timeout=30, stream=True)
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
        """Get total number of images in GitHub repository

        Returns
        -------
        int or None
            The total number of images, or None if unable to determine.
        """
        try:
            count = 0
            image_extensions = {
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".bmp",
                ".webp",
                ".svg",
            }

            # Use iterative approach for counting as well
            paths_to_process = [
                self.config.path.rstrip("/") if self.config.path else ""
            ]
            processed_paths = set()

            while paths_to_process:
                path = paths_to_process.pop(0)

                # Avoid processing the same path multiple times
                if path in processed_paths:
                    continue
                processed_paths.add(path)

                headers = {
                    "Authorization": f"token {self.config.token}",
                    "Accept": "application/vnd.github.v3+json",
                }

                url = f"{self.api_base}/repos/{self.config.owner}/{self.config.repo}/contents"
                if path:
                    url += f"/{path}"

                response = requests.get(url, headers=headers, timeout=30)

                if response.status_code != 200:
                    self.logger.warning(
                        f"Unable to get GitHub directory contents for counting: {path}"
                    )
                    continue

                contents = response.json()

                for item in contents:
                    if item["type"] == "file":
                        file_path = item["path"]
                        file_ext = Path(file_path).suffix.lower()

                        # Check if path matches configured path prefix
                        if self.config.path and not file_path.startswith(
                            self.config.path
                        ):
                            continue

                        if file_ext in image_extensions:
                            count += 1
                    elif item["type"] == "dir":
                        # Add subdirectory to processing queue
                        paths_to_process.append(item["path"])

            return count
        except Exception as e:
            self.logger.warning(f"Failed to get total number of GitHub images: {e}")
            return None
