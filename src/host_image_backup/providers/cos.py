"""腾讯云COS提供商

This module provides the implementation for Tencent Cloud COS image hosting.
"""

from qcloud_cos import CosConfig, CosS3Client
from typing import Iterator, Optional
from pathlib import Path
import requests

from loguru import logger

from .base import BaseProvider, ImageInfo
from ..config import COSConfig


class COSProvider(BaseProvider):
    """腾讯云COS提供商"""
    
    def __init__(self, config: COSConfig):
        super().__init__(config)
        self.config: COSConfig = config
        self.logger = logger
        self._client = None
    
    @property
    def client(self) -> CosS3Client:
        """获取COS客户端
        
        Returns
        -------
        CosS3Client
            The COS client instance.
        """
        if self._client is None:
            cos_config = CosConfig(
                Region=self.config.region,
                SecretId=self.config.secret_id,
                SecretKey=self.config.secret_key
            )
            self._client = CosS3Client(cos_config)
        return self._client
    
    def test_connection(self) -> bool:
        """测试COS连接
        
        Returns
        -------
        bool
            True if connection is successful, False otherwise.
        """
        try:
            # 尝试获取bucket信息
            response = self.client.head_bucket(Bucket=self.config.bucket)
            return response['ResponseMetadata']['HTTPStatusCode'] == 200
        except Exception as e:
            self.logger.error(f"COS连接测试失败: {e}")
            return False
    
    def list_images(self, limit: Optional[int] = None) -> Iterator[ImageInfo]:
        """列出COS中的所有图片
        
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
            marker = ""
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
            
            while True:
                if limit and count >= limit:
                    break
                
                # 获取对象列表
                response = self.client.list_objects(
                    Bucket=self.config.bucket,
                    Prefix=self.config.prefix,
                    Marker=marker,
                    MaxKeys=1000
                )
                
                if 'Contents' not in response:
                    break
                
                for obj in response['Contents']:
                    if limit and count >= limit:
                        break
                    
                    key = obj['Key']
                    file_ext = Path(key).suffix.lower()
                    
                    if file_ext not in image_extensions:
                        continue
                    
                    # 构造图片URL
                    url = f"https://{self.config.bucket}.cos.{self.config.region}.myqcloud.com/{key}"
                    
                    yield ImageInfo(
                        url=url,
                        filename=Path(key).name,
                        size=obj.get('Size'),
                        created_at=obj.get('LastModified'),
                        metadata={
                            'key': key,
                            'etag': obj.get('ETag', '').strip('"'),
                            'storage_class': obj.get('StorageClass')
                        }
                    )
                    count += 1
                
                # 检查是否还有更多对象
                if response.get('IsTruncated') == 'false':
                    break
                
                marker = response.get('NextMarker', '')
                if not marker and response.get('Contents'):
                    marker = response['Contents'][-1]['Key']
                
        except Exception as e:
            self.logger.error(f"列出COS图片失败: {e}")
            raise
    
    def download_image(self, image_info: ImageInfo, output_path: Path) -> bool:
        """从COS下载图片
        
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
                # 直接从COS下载
                response = self.client.get_object(
                    Bucket=self.config.bucket,
                    Key=key
                )
                
                with open(output_path, 'wb') as f:
                    for chunk in response['Body'].iter_chunks():
                        f.write(chunk)
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
        """获取COS中的图片总数
        
        Returns
        -------
        int or None
            The total number of images, or None if unable to determine.
        """
        try:
            count = 0
            marker = ""
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
            
            while True:
                response = self.client.list_objects(
                    Bucket=self.config.bucket,
                    Prefix=self.config.prefix,
                    Marker=marker,
                    MaxKeys=1000
                )
                
                if 'Contents' not in response:
                    break
                
                for obj in response['Contents']:
                    key = obj['Key']
                    file_ext = Path(key).suffix.lower()
                    if file_ext in image_extensions:
                        count += 1
                
                if response.get('IsTruncated') == 'false':
                    break
                
                marker = response.get('NextMarker', '')
                if not marker and response.get('Contents'):
                    marker = response['Contents'][-1]['Key']
            
            return count
        except Exception as e:
            self.logger.warning(f"获取COS图片总数失败: {e}")
            return None
