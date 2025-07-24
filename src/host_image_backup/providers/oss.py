import oss2
from typing import Iterator, Optional
from pathlib import Path
import requests

from loguru import logger

from .base import BaseProvider, ImageInfo
from ..config import OSSConfig


class OSSProvider(BaseProvider):
    """Alibaba Cloud OSS Provider"""
    
    def __init__(self, config: OSSConfig):
        super().__init__(config)
        self.config: OSSConfig = config
        self.logger = logger
        self._bucket = None
    
    @property
    def bucket(self) -> oss2.Bucket:
        """Get OSS bucket instance
        
        Returns
        -------
        oss2.Bucket
            The OSS bucket instance.
        """
        if self._bucket is None:
            auth = oss2.Auth(self.config.access_key_id, self.config.access_key_secret)
            self._bucket = oss2.Bucket(auth, self.config.endpoint, self.config.bucket)
        return self._bucket
    
    def test_connection(self) -> bool:
        """Test OSS connection
        
        Returns
        -------
        bool
            True if connection is successful, False otherwise.
        """
        try:
            # Try to get bucket information
            self.bucket.get_bucket_info()
            return True
        except Exception as e:
            self.logger.error(f"OSS connection test failed: {e}")
            return False
    
    def list_images(self, limit: Optional[int] = None) -> Iterator[ImageInfo]:
        """List all images in OSS
        
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
            # Supported image extensions
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
            
            for obj in oss2.ObjectIterator(self.bucket, prefix=self.config.prefix):
                if limit and count >= limit:
                    break
                
                # Check if it's an image file
                file_ext = Path(obj.key).suffix.lower()
                if file_ext not in image_extensions:
                    continue
                
                # Construct image URL
                url = f"https://{self.config.bucket}.{self.config.endpoint}/{obj.key}"
                
                yield ImageInfo(
                    url=url,
                    filename=Path(obj.key).name,
                    size=obj.size,
                    created_at=obj.last_modified.isoformat() if obj.last_modified else None,
                    metadata={
                        'key': obj.key,
                        'etag': obj.etag,
                        'storage_class': obj.storage_class
                    }
                )
                count += 1
                
        except Exception as e:
            self.logger.error(f"Failed to list OSS images: {e}")
            raise
    
    def download_image(self, image_info: ImageInfo, output_path: Path) -> bool:
        """Download image from OSS
        
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
            # Extract key from metadata
            key = image_info.metadata.get('key') if image_info.metadata else None
            if not key:
                key = image_info.filename
            
            # Download image
            self.bucket.get_object_to_file(key, str(output_path))
            return True
        except Exception as e:
            self.logger.error(f"Failed to download image {image_info.url}: {e}")
            return False
    
    def get_image_count(self) -> Optional[int]:
        """Get total number of images in OSS
        
        Returns
        -------
        int or None
            The total number of images, or None if unable to determine.
        """
        try:
            count = 0
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
            
            for obj in oss2.ObjectIterator(self.bucket, prefix=self.config.prefix):
                file_ext = Path(obj.key).suffix.lower()
                if file_ext in image_extensions:
                    count += 1
            
            return count
        except Exception as e:
            self.logger.warning(f"Failed to get total number of OSS images: {e}")
            return None
