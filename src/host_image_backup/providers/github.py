"""GitHub Provider

This module provides the implementation for GitHub image hosting.
"""

from collections.abc import Iterator
from pathlib import Path

import requests
from loguru import logger

from ..config import GitHubConfig
from .base import BaseProvider, ImageInfo


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
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get(
                f"{self.api_base}/repos/{self.config.owner}/{self.config.repo}",
                headers=headers,
                timeout=10
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
            "Accept": "application/vnd.github.v3+json"
        }
        count = 0
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"}

        # Recursively get directory contents
        def get_files(path: str = ""):
            nonlocal count

            if limit and count >= limit:
                return

            url = f"{self.api_base}/repos/{self.config.owner}/{self.config.repo}/contents"
            if path:
                url += f"/{path}"

            try:
                response = requests.get(url, headers=headers, timeout=30)

                if response.status_code != 200:
                    self.logger.warning(f"Unable to get GitHub directory contents: {path}, Status code: {response.status_code}")
                    return

                contents = response.json()

                for item in contents:
                    if limit and count >= limit:
                        break

                    if item["type"] == "file":
                        file_path = item["path"]
                        file_ext = Path(file_path).suffix.lower()

                        # Check if path matches configured path prefix
                        if self.config.path and not file_path.startswith(self.config.path):
                            continue

                        if file_ext in image_extensions:
                            # Construct image URL
                            url = item["download_url"]

                            yield ImageInfo(
                                url=url,
                                filename=Path(file_path).name,
                                size=item.get("size"),
                                created_at=None,  # GitHub API doesn't provide creation time
                                metadata={
                                    "sha": item.get("sha"),
                                    "path": file_path
                                }
                            )
                            count += 1

                    elif item["type"] == "dir":
                        # Recursively process subdirectories
                        get_files(item["path"])

            except Exception as e:
                self.logger.error(f"Error listing GitHub files: {e}")

        get_files(self.config.path.rstrip("/") if self.config.path else "")
