"""Imgur图床提供商

This module provides the implementation for Imgur image hosting.
"""

import requests
from typing import Iterator, Optional
from pathlib import Path
import time

from loguru import logger

from .base import BaseProvider, ImageInfo
from ..config import ImgurConfig


class ImgurProvider(BaseProvider):
    """Imgur图床提供商"""
    
    def __init__(self, config: ImgurConfig):
        super().__init__(config)
        self.config: ImgurConfig = config
        self.logger = logger
        self.api_base = "https://api.imgur.com/3"
    
    def test_connection(self) -> bool:
        """测试Imgur连接
        
        Returns
        -------
        bool
            True if connection is successful, False otherwise.
        """
        try:
            headers = {'Authorization': f'Bearer {self.config.access_token}'}
            response = requests.get(
                f"{self.api_base}/account/me",
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Imgur连接测试失败: {e}")
            return False
    
    def list_images(self, limit: Optional[int] = None) -> Iterator[ImageInfo]:
        """列出Imgur中的所有图片
        
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
            headers = {'Authorization': f'Bearer {self.config.access_token}'}
            count = 0
            page = 0
            
            while True:
                if limit and count >= limit:
                    break
                
                # 获取用户的图片
                response = requests.get(
                    f"{self.api_base}/account/me/images/{page}",
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code != 200:
                    self.logger.error(f"获取Imgur图片列表失败: {response.status_code}")
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
                    
                    # 获取文件名（从title或者link中提取）
                    filename = img.get('title') or Path(img['link']).name
                    if not filename.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                        filename += f".{img.get('type', 'jpg').split('/')[-1]}"
                    
                    yield ImageInfo(
                        url=img['link'],
                        filename=filename,
                        size=img.get('size'),
                        created_at=img.get('datetime'),
                        metadata={
                            'id': img['id'],
                            'title': img.get('title'),
                            'description': img.get('description'),
                            'type': img.get('type'),
                            'width': img.get('width'),
                            'height': img.get('height'),
                            'views': img.get('views'),
                            'deletehash': img.get('deletehash')
                        }
                    )
                    count += 1
                
                # 如果返回的图片数量为0，说明没有更多图片了
                if len(images) == 0:
                    break
                
                page += 1
                
                # 避免频繁请求，添加延迟
                time.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"列出Imgur图片失败: {e}")
            raise
    
    def download_image(self, image_info: ImageInfo, output_path: Path) -> bool:
        """从Imgur下载图片
        
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
            # 确保输出目录存在
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
            
            self.logger.debug(f"成功下载图片: {image_info.filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"下载图片失败 {image_info.filename}: {e}")
            return False
    
    def get_image_count(self) -> Optional[int]:
        """获取Imgur中的图片总数
        
        Returns
        -------
        int or None
            The total number of images, or None if unable to determine.
        """
        try:
            headers = {'Authorization': f'Bearer {self.config.access_token}'}
            response = requests.get(
                f"{self.api_base}/account/me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    account_data = data.get('data', {})
                    return account_data.get('total_images', 0)
            
            return None
        except Exception as e:
            self.logger.warning(f"获取Imgur图片总数失败: {e}")
            return None
