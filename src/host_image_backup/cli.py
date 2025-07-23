"""命令行界面模块

This module provides the command-line interface for the host image backup tool
using Typer for argument parsing and command management.
"""

import typer
from pathlib import Path
from typing import Optional

from loguru import logger

from .config import AppConfig
from .service import BackupService


def setup_logging(verbose: bool = False) -> None:
    """设置日志
    
    Parameters
    ----------
    verbose : bool, default=False
        Whether to enable verbose logging.
    """
    level = "DEBUG" if verbose else "INFO"
    logger.remove()  # Remove default handler
    logger.add(
        "logs/host_image_backup_{time}.log",
        rotation="10 MB",
        retention="1 week",
        compression="zip",
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    )
    logger.add(
        lambda msg: print(msg, end=""),
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )


app = typer.Typer(
    name="host-image-backup",
    help="Host Image Backup - 图床备份工具",
    no_args_is_help=True
)


@app.callback()
def main(
    config: Optional[Path] = typer.Option(None, "--config", "-c", exists=True, help="配置文件路径"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细日志")
) -> None:
    """Host Image Backup - 图床备份工具"""
    setup_logging(verbose)
    
    # 加载配置
    app_config = AppConfig.load(config)
    
    # 创建备份服务
    backup_service = BackupService(app_config)
    
    # Store in app context
    app.config = app_config
    app.service = backup_service
    app.verbose = verbose


@app.command()
def init() -> None:
    """初始化配置文件"""
    config: AppConfig = app.config
    
    # 创建默认配置
    config.create_default_config()
    
    config_file = AppConfig.get_config_file()
    typer.echo(f"✅ 配置文件已创建: {config_file}")
    typer.echo("请编辑配置文件，添加你的图床配置信息。")
    
    # 显示配置文件示例
    typer.echo("\n配置文件示例：")
    typer.echo("""
# 应用配置
default_output_dir: "./backup"
max_concurrent_downloads: 5
timeout: 30
retry_count: 3
log_level: "INFO"

# 提供商配置
providers:
  oss:
    enabled: true
    prefix: "images/"
    access_key_id: "your_access_key"
    access_key_secret: "your_secret_key"
    bucket: "your_bucket_name"
    endpoint: "oss-cn-hangzhou.aliyuncs.com"
  
  cos:
    enabled: true
    prefix: "images/"
    secret_id: "your_secret_id"
    secret_key: "your_secret_key"
    bucket: "your_bucket_name"
    region: "ap-guangzhou"
  
  sms:
    enabled: true
    api_token: "your_api_token"
  
  imgur:
    enabled: true
    client_id: "your_client_id"
    client_secret: "your_client_secret"
    access_token: "your_access_token"
    refresh_token: "your_refresh_token"
  
  github:
    enabled: true
    token: "your_github_token"
    owner: "your_username"
    repo: "your_repo_name"
    path: "images/"
""")


@app.command()
def backup(
    provider: str = typer.Argument(..., help="提供商名称"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="输出目录"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="限制下载数量"),
    skip_existing: bool = typer.Option(True, "--skip-existing/--no-skip-existing", help="跳过已存在的文件")
) -> None:
    """备份指定提供商的图片"""
    service: BackupService = app.service
    config: AppConfig = app.config
    verbose: bool = app.verbose
    
    # 检查提供商是否存在
    if provider not in service.list_providers():
        typer.echo(f"❌ 未知的提供商: {provider}")
        typer.echo(f"可用的提供商: {', '.join(service.list_providers())}")
        raise typer.Exit(code=1)
    
    # 设置输出目录
    output_dir = output if output else Path(config.default_output_dir)
    
    typer.echo(f"开始备份 {provider} 的图片到 {output_dir}")
    
    if limit:
        typer.echo(f"限制下载数量: {limit}")
    
    if skip_existing:
        typer.echo("跳过已存在的文件")
    
    # 执行备份
    success = service.backup_images(
        provider_name=provider,
        output_dir=output_dir,
        limit=limit,
        skip_existing=skip_existing,
        verbose=verbose
    )
    
    if success:
        typer.echo("✅ 备份完成")
    else:
        typer.echo("❌ 备份过程中出现错误")
        raise typer.Exit(code=1)


@app.command("list-providers")
def list_providers() -> None:
    """列出所有可用的提供商"""
    service: BackupService = app.service
    config: AppConfig = app.config
    
    providers = service.list_providers()
    
    typer.echo("可用的提供商：")
    for provider_name in providers:
        status = "✅" if provider_name in config.providers and config.providers[provider_name].enabled else "❌"
        typer.echo(f"  {status} {provider_name}")


@app.command()
def test(provider: str = typer.Argument(..., help="提供商名称")) -> None:
    """测试提供商连接"""
    service: BackupService = app.service
    
    if provider not in service.list_providers():
        typer.echo(f"❌ 未知的提供商: {provider}")
        raise typer.Exit(code=1)
    
    typer.echo(f"测试 {provider} 连接...")
    success = service.test_provider(provider)
    
    if not success:
        raise typer.Exit(code=1)


@app.command()
def info(provider: str = typer.Argument(..., help="提供商名称")) -> None:
    """显示提供商详细信息"""
    service: BackupService = app.service
    
    if provider not in service.list_providers():
        typer.echo(f"❌ 未知的提供商: {provider}")
        raise typer.Exit(code=1)
    
    service.show_provider_info(provider)


@app.command("backup-all")
def backup_all(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="输出目录"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="每个提供商的限制下载数量"),
    skip_existing: bool = typer.Option(True, "--skip-existing/--no-skip-existing", help="跳过已存在的文件")
) -> None:
    """备份所有启用的提供商的图片"""
    service: BackupService = app.service
    config: AppConfig = app.config
    verbose: bool = app.verbose
    
    # 设置输出目录
    output_dir = output if output else Path(config.default_output_dir)
    
    # 获取所有启用的提供商
    enabled_providers = [
        name for name, provider_config in config.providers.items()
        if provider_config.enabled and provider_config.validate_config()
    ]
    
    if not enabled_providers:
        typer.echo("❌ 没有启用且配置有效的提供商")
        raise typer.Exit(code=1)
    
    typer.echo(f"将备份以下提供商: {', '.join(enabled_providers)}")
    typer.echo(f"输出目录: {output_dir}")
    
    success_count = 0
    
    for provider_name in enabled_providers:
        typer.echo(f"\n开始备份 {provider_name}...")
        
        success = service.backup_images(
            provider_name=provider_name,
            output_dir=output_dir,
            limit=limit,
            skip_existing=skip_existing,
            verbose=verbose
        )
        
        if success:
            success_count += 1
        else:
            typer.echo(f"❌ {provider_name} 备份失败")
    
    typer.echo(f"\n备份完成: {success_count}/{len(enabled_providers)} 个提供商备份成功")
    
    if success_count < len(enabled_providers):
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
