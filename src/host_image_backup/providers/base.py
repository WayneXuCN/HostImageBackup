"""图床提供商基类

This module provides the base class for all image hosting providers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Iterator
from dataclasses import dataclass
from pathlib import Path

from loguru import logger


@dataclass
class ImageInfo:
    """图片信息
    
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
    size: Optional[int] = None
    created_at: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseProvider(ABC):
    """图床提供商基类
    
    This is the base class that all provider implementations should inherit from.
    """
    
    def __init__(self, config: Any):
        """初始化提供商
        
        Parameters
        ----------
        config : Any
            The provider configuration object.
        """
        self.config = config
        self.logger = logger
    
    @abstractmethod
    def test_connection(self) -> bool:
        """测试连接是否正常
        
        Returns
        -------
        bool
            True if connection is successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def list_images(self, limit: Optional[int] = None) -> Iterator[ImageInfo]:
        """列出所有图片
        
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
        """下载图片到本地
        
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
    
    def get_image_count(self) -> Optional[int]:
        """获取图片总数
        
        Returns
        -------
        int or None
            The total number of images, or None if unable to determine.
        """
        # 默认实现：遍历所有图片计数（可能很慢）
        try:
            count = 0
            for _ in self.list_images():
                count += 1
            return count
        except Exception as e:
            self.logger.warning(f"无法获取图片总数: {e}")
            return None
    
    def validate_config(self) -> bool:
        """验证配置是否有效
        
        Returns
        -------
        bool
            True if configuration is valid, False otherwise.
        """
        return self.config.validate_config()
    
    def get_provider_name(self) -> str:
        """获取提供商名称
        
        Returns
        -------
        str
            The name of the provider.
        """
        return self.config.name
    
    def is_enabled(self) -> bool:
        """检查提供商是否启用
        
        Returns
        -------
        bool
            True if provider is enabled, False otherwise.
        """
        return self.config.enabled
