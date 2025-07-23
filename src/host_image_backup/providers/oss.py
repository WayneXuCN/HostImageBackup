"""阿里云OSS提供商

This module provides the implementation for Alibaba Cloud OSS image hosting.
"""

import oss2
from typing import Iterator, Optional
from pathlib import Path
import requests

from loguru import logger

from .base import BaseProvider, ImageInfo
from ..config import OSSConfig


class OSSProvider(BaseProvider):
    """阿里云OSS提供商"""
    
    def __init__(self, config: OSSConfig):
        super().__init__(config)
        self.config: OSSConfig = config
        self.logger = logger
        self._bucket = None
    
    @property
    def bucket(self) -> oss2.Bucket:
        """获取OSS bucket实例
        
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
        """测试OSS连接
        
        Returns
        -------
        bool
            True if connection is successful, False otherwise.
        """
        try:
            # 尝试获取bucket信息
            self.bucket.get_bucket_info()
            return True
        except Exception as e:
            self.logger.error(f"OSS连接测试失败: {e}")
            return False
    
    def list_images(self, limit: Optional[int] = None) -> Iterator[ImageInfo]:
        """列出OSS中的所有图片
        
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
            # 支持的图片扩展名
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
            
            for obj in oss2.ObjectIterator(self.bucket, prefix=self.config.prefix):
                if limit and count >= limit:
                    break
                
                # 检查是否为图片文件
                file_ext = Path(obj.key).suffix.lower()
                if file_ext not in image_extensions:
                    continue
                
                # 构造图片URL
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
            self.logger.error(f"列出OSS图片失败: {e}")
            raise
    
    def download_image(self, image_info: ImageInfo, output_path: Path) -> bool:
        """从OSS下载图片
        
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
            
            # 从metadata中获取key
            key = image_info.metadata.get('key') if image_info.metadata else None
            
            if key:
                # 直接从OSS下载
                self.bucket.get_object_to_file(key, str(output_path))
            else:
                # 通过URL下载
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
        """获取OSS中的图片总数
        
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
            self.logger.warning(f"获取OSS图片总数失败: {e}")
            return None
