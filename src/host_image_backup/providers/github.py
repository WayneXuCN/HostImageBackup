"""GitHub图床提供商

This module provides the implementation for GitHub image hosting.
"""

import requests
from typing import Iterator, Optional
from pathlib import Path
import time

from loguru import logger

from .base import BaseProvider, ImageInfo
from ..config import GitHubConfig


class GitHubProvider(BaseProvider):
    """GitHub图床提供商"""
    
    def __init__(self, config: GitHubConfig):
        super().__init__(config)
        self.config: GitHubConfig = config
        self.logger = logger
        self.api_base = "https://api.github.com"
    
    def test_connection(self) -> bool:
        """测试GitHub连接
        
        Returns
        -------
        bool
            True if connection is successful, False otherwise.
        """
        try:
            headers = {
                'Authorization': f'token {self.config.token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.get(
                f"{self.api_base}/repos/{self.config.owner}/{self.config.repo}",
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"GitHub连接测试失败: {e}")
            return False
    
    def list_images(self, limit: Optional[int] = None) -> Iterator[ImageInfo]:
        """列出GitHub仓库中的所有图片
        
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
            'Authorization': f'token {self.config.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        count = 0
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
        
        # 递归获取目录内容
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
                    self.logger.warning(f"无法获取GitHub目录内容: {path}, 状态码: {response.status_code}")
                    return
                
                contents = response.json()
                
                for item in contents:
                    if limit and count >= limit:
                        break
                    
                    if item['type'] == 'file':
                        file_path = item['path']
                        file_ext = Path(file_path).suffix.lower()
                        
                        # 检查路径是否匹配配置的路径前缀
                        if self.config.path and not file_path.startswith(self.config.path):
                            continue
                        
                        if file_ext in image_extensions:
                            yield ImageInfo(
                                url=item['download_url'],
                                filename=item['name'],
                                size=item['size'],
                                metadata={
                                    'path': item['path'],
                                    'sha': item['sha'],
                                    'git_url': item['git_url'],
                                    'html_url': item['html_url']
                                }
                            )
                            count += 1
                    
                    elif item['type'] == 'dir':
                        # 递归处理子目录
                        yield from get_files(item['path'])
            
            except Exception as e:
                self.logger.error(f"获取GitHub目录内容失败: {path}, 错误: {e}")
                return
        
        # 从配置的路径开始
        start_path = self.config.path.strip('/') if self.config.path else ""
        yield from get_files(start_path)
    
    def download_image(self, image_info: ImageInfo, output_path: Path) -> bool:
        """从GitHub下载图片
        
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
        """获取GitHub仓库中的图片总数
        
        Returns
        -------
        int or None
            The total number of images, or None if unable to determine.
        """
        try:
            count = 0
            for _ in self.list_images():
                count += 1
            return count
        except Exception as e:
            self.logger.warning(f"获取GitHub图片总数失败: {e}")
            return None
