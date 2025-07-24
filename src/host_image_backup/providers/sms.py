import requests
from typing import Iterator, Optional
from pathlib import Path
import time

from loguru import logger

from .base import BaseProvider, ImageInfo
from ..config import SMSConfig


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
            headers = {'Authorization': self.config.api_token}
            response = requests.get(
                f"{self.api_base}/profile",
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"SM.MS connection test failed: {e}")
            return False
    
    def list_images(self, limit: Optional[int] = None) -> Iterator[ImageInfo]:
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
            headers = {'Authorization': self.config.api_token}
            count = 0
            
            # SM.MS API limit, maximum 100 images returned per request
            page = 0
            per_page = 100
            
            while True:
                if limit and count >= limit:
                    break
                
                response = requests.get(
                    f"{self.api_base}/upload_history",
                    headers=headers,
                    params={
                        'page': page,
                        'format': 'json'
                    },
                    timeout=30
                )
                
                if response.status_code != 200:
                    self.logger.error(f"Failed to get SM.MS image list: {response.status_code}")
                    break
                
                data = response.json()
                
                if not data.get('success') or not data.get('data'):
                    break
                
                images = data['data']
                if not images:
                    break
                
                for img in images:
                    if limit and count >= limit:
                        break
                    
                    yield ImageInfo(
                        url=img['url'],
                        filename=img['filename'],
                        size=img.get('size'),
                        created_at=img.get('created_at'),
                        metadata={
                            'hash': img.get('hash'),
                            'delete_url': img.get('delete'),
                            'page_url': img.get('page')
                        }
                    )
                    count += 1
                
                # If the number of returned images is less than the requested number, there are no more images
                if len(images) < per_page:
                    break
                
                page += 1
                
                # Add delay to avoid rate limiting
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
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            response = requests.get(
                image_info.url,
                timeout=30,
                stream=True
            )
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.debug(f"Successfully downloaded image: {image_info.filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download image {image_info.filename}: {e}")
            return False
    
    def get_image_count(self) -> Optional[int]:
        """Get the total number of images in SM.MS
        
        Returns
        -------
        int or None
            The total number of images, or None if unable to determine.
        """
        try:
            headers = {'Authorization': self.config.api_token}
            response = requests.get(
                f"{self.api_base}/profile",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    profile = data.get('data', {})
                    return profile.get('disk_usage_raw', {}).get('upload_count')
            
            return None
        except Exception as e:
            self.logger.warning(f"Failed to get SM.MS image total count: {e}")
            return None