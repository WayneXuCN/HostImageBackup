"""备份服务模块

This module provides the main backup service that orchestrates the backup
process for different image hosting providers.
"""

import concurrent.futures
from pathlib import Path
from typing import Optional, List
from tqdm import tqdm
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from loguru import logger

from .config import AppConfig
from .providers import BaseProvider, ImageInfo
from .providers.oss import OSSProvider
from .providers.cos import COSProvider
from .providers.sms import SMSProvider
from .providers.imgur import ImgurProvider
from .providers.github import GitHubProvider


class BackupService:
    """备份服务"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.console = Console()
        self.logger = logger
        
        # 初始化提供商映射
        self.provider_classes = {
            'oss': OSSProvider,
            'cos': COSProvider,
            'sms': SMSProvider,
            'imgur': ImgurProvider,
            'github': GitHubProvider
        }
    
    def get_provider(self, provider_name: str) -> Optional[BaseProvider]:
        """获取提供商实例"""
        if provider_name not in self.config.providers:
            self.logger.error(f"未找到提供商配置: {provider_name}")
            return None
        
        provider_config = self.config.providers[provider_name]
        
        if not provider_config.enabled:
            self.logger.error(f"提供商未启用: {provider_name}")
            return None
        
        if not provider_config.validate_config():
            self.logger.error(f"提供商配置无效: {provider_name}")
            return None
        
        provider_class = self.provider_classes.get(provider_name)
        if not provider_class:
            self.logger.error(f"未找到提供商实现: {provider_name}")
            return None
        
        return provider_class(provider_config)
    
    def list_providers(self) -> List[str]:
        """列出所有可用的提供商"""
        return list(self.provider_classes.keys())
    
    def test_provider(self, provider_name: str) -> bool:
        """测试提供商连接"""
        provider = self.get_provider(provider_name)
        if not provider:
            return False
        
        try:
            result = provider.test_connection()
            if result:
                self.console.print(f"✅ {provider_name} 连接测试成功", style="green")
            else:
                self.console.print(f"❌ {provider_name} 连接测试失败", style="red")
            return result
        except Exception as e:
            self.console.print(f"❌ {provider_name} 连接测试异常: {e}", style="red")
            return False
    
    def backup_images(
        self,
        provider_name: str,
        output_dir: Path,
        limit: Optional[int] = None,
        skip_existing: bool = True,
        verbose: bool = False
    ) -> bool:
        """备份图片"""
        provider = self.get_provider(provider_name)
        if not provider:
            return False
        
        try:
            # 创建输出目录
            output_dir = Path(output_dir)
            provider_dir = output_dir / provider_name
            provider_dir.mkdir(parents=True, exist_ok=True)
            
            # 获取图片总数（用于进度条）
            total_count = provider.get_image_count()
            if limit and total_count:
                total_count = min(total_count, limit)
            
            # 初始化进度条
            progress_bar = tqdm(
                total=total_count,
                desc=f"备份 {provider_name}",
                unit="张",
                leave=True
            )
            
            success_count = 0
            error_count = 0
            skip_count = 0
            
            # 创建线程池执行器
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.config.max_concurrent_downloads
            ) as executor:
                
                futures = []
                
                for image_info in provider.list_images(limit=limit):
                    # 构建输出文件路径
                    output_file = provider_dir / self._sanitize_filename(image_info.filename)
                    
                    # 如果文件已存在且设置了跳过，则跳过
                    if skip_existing and output_file.exists():
                        skip_count += 1
                        progress_bar.update(1)
                        if verbose:
                            self.console.print(f"跳过已存在文件: {image_info.filename}", style="yellow")
                        continue
                    
                    # 提交下载任务
                    future = executor.submit(
                        self._download_image_with_retry,
                        provider,
                        image_info,
                        output_file,
                        verbose
                    )
                    futures.append(future)
                
                # 等待所有下载任务完成
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                    except Exception as e:
                        error_count += 1
                        if verbose:
                            self.logger.error(f"下载任务异常: {e}")
                    
                    progress_bar.update(1)
            
            progress_bar.close()
            
            # 显示备份结果
            self._show_backup_summary(provider_name, success_count, error_count, skip_count)
            
            return error_count == 0
            
        except Exception as e:
            self.logger.error(f"备份过程异常: {e}")
            return False
    
    def _download_image_with_retry(
        self,
        provider: BaseProvider,
        image_info: ImageInfo,
        output_file: Path,
        verbose: bool
    ) -> bool:
        """带重试的下载图片"""
        for attempt in range(self.config.retry_count):
            try:
                result = provider.download_image(image_info, output_file)
                if result:
                    if verbose:
                        self.console.print(f"✅ 下载成功: {image_info.filename}", style="green")
                    return True
                else:
                    if verbose:
                        self.console.print(f"❌ 下载失败: {image_info.filename} (尝试 {attempt + 1}/{self.config.retry_count})", style="red")
            except Exception as e:
                if verbose:
                    self.console.print(f"❌ 下载异常: {image_info.filename} (尝试 {attempt + 1}/{self.config.retry_count}): {e}", style="red")
        
        return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        # 替换非法字符
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        
        # 限制文件名长度
        if len(filename) > 255:
            name, ext = Path(filename).stem, Path(filename).suffix
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    def _show_backup_summary(self, provider_name: str, success: int, error: int, skip: int) -> None:
        """显示备份摘要"""
        table = Table(title=f"{provider_name} 备份结果")
        
        table.add_column("项目", style="cyan", no_wrap=True)
        table.add_column("数量", style="magenta")
        
        table.add_row("成功下载", str(success))
        table.add_row("下载失败", str(error))
        table.add_row("跳过文件", str(skip))
        table.add_row("总计", str(success + error + skip))
        
        self.console.print(table)
        
        if error > 0:
            self.console.print(
                Panel(
                    f"有 {error} 个文件下载失败，请检查网络连接或提供商配置",
                    title="警告",
                    style="yellow"
                )
            )
    
    def show_provider_info(self, provider_name: str) -> None:
        """显示提供商信息"""
        provider = self.get_provider(provider_name)
        if not provider:
            self.console.print(f"❌ 无法获取提供商: {provider_name}", style="red")
            return
        
        # 测试连接
        connection_status = "✅ 正常" if provider.test_connection() else "❌ 失败"
        
        # 获取图片数量
        try:
            image_count = provider.get_image_count()
            count_text = str(image_count) if image_count is not None else "无法获取"
        except Exception:
            count_text = "获取失败"
        
        table = Table(title=f"{provider_name.upper()} 提供商信息")
        table.add_column("属性", style="cyan")
        table.add_column("值", style="magenta")
        
        table.add_row("名称", provider_name.upper())
        table.add_row("状态", "启用" if provider.is_enabled() else "禁用")
        table.add_row("连接测试", connection_status)
        table.add_row("图片数量", count_text)
        table.add_row("配置有效", "是" if provider.validate_config() else "否")
        
        self.console.print(table)
