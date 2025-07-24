import typer
from pathlib import Path
from typing import Optional

from loguru import logger

from .config import AppConfig
from .service import BackupService


def setup_logging(verbose: bool = False) -> None:
    """Setup logging

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
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    )
    logger.add(
        lambda msg: print(msg, end=""),
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )


app = typer.Typer(
    name="host-image-backup",
    help="Host Image Backup - Image Hosting Backup Tool",
    no_args_is_help=True,
)


@app.callback()
def main(
    config: Optional[Path] = typer.Option(
        None, "--config", "-c", exists=True, help="Configuration file path"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed logs"),
) -> None:
    """Host Image Backup - Image Hosting Backup Tool"""
    setup_logging(verbose)

    # Load configuration
    app_config = AppConfig.load(config)

    # Create backup service
    backup_service = BackupService(app_config)

    # Store in app context
    app.config = app_config
    app.service = backup_service
    app.verbose = verbose


@app.command()
def init() -> None:
    """Initialize configuration file"""
    config: AppConfig = app.config

    # Create default configuration
    config.create_default_config()

    config_file = AppConfig.get_config_file()
    typer.echo(f"✅ Configuration file created: {config_file}")
    typer.echo(
        "Please edit the configuration file and add your image hosting configuration information."
    )

    # Show configuration file example
    typer.echo("\nConfiguration file example:")
    typer.echo("""
# Application configuration
default_output_dir: "./backup"
max_concurrent_downloads: 5
timeout: 30
retry_count: 3
log_level: "INFO"

# Provider configuration
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
    provider: str = typer.Argument(..., help="Provider name"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
    limit: Optional[int] = typer.Option(
        None, "--limit", "-l", help="Limit download count"
    ),
    skip_existing: bool = typer.Option(
        True, "--skip-existing/--no-skip-existing", help="Skip existing files"
    ),
) -> None:
    """Backup images from the specified provider"""
    service: BackupService = app.service
    config: AppConfig = app.config
    verbose: bool = app.verbose

    # Check if provider exists
    if provider not in service.list_providers():
        typer.echo(f"❌ Unknown provider: {provider}")
        typer.echo(f"Available providers: {', '.join(service.list_providers())}")
        raise typer.Exit(code=1)

    # Set output directory
    output_dir = output if output else Path(config.default_output_dir)

    typer.echo(f"Starting to backup images from {provider} to {output_dir}")

    if limit:
        typer.echo(f"Limit download count: {limit}")

    if skip_existing:
        typer.echo("Skip existing files")

    # Execute backup
    success = service.backup_images(
        provider_name=provider,
        output_dir=output_dir,
        limit=limit,
        skip_existing=skip_existing,
        verbose=verbose,
    )

    if success:
        typer.echo("✅ Backup completed")
    else:
        typer.echo("❌ Errors occurred during backup")
        raise typer.Exit(code=1)


@app.command("list-providers")
def list_providers() -> None:
    """List all available providers"""
    service: BackupService = app.service
    config: AppConfig = app.config

    providers = service.list_providers()

    typer.echo("Available providers:")
    for provider_name in providers:
        status = (
            "✅"
            if provider_name in config.providers
            and config.providers[provider_name].enabled
            else "❌"
        )
        typer.echo(f"  {status} {provider_name}")


@app.command()
def test(provider: str = typer.Argument(..., help="Provider name")) -> None:
    """Test provider connection"""
    service: BackupService = app.service

    if provider not in service.list_providers():
        typer.echo(f"❌ Unknown provider: {provider}")
        raise typer.Exit(code=1)

    typer.echo(f"Testing {provider} connection...")
    success = service.test_provider(provider)

    if not success:
        raise typer.Exit(code=1)


@app.command()
def info(provider: str = typer.Argument(..., help="Provider name")) -> None:
    """Show provider detailed information"""
    service: BackupService = app.service

    if provider not in service.list_providers():
        typer.echo(f"❌ Unknown provider: {provider}")
        raise typer.Exit(code=1)

    service.show_provider_info(provider)


@app.command("backup-all")
def backup_all(
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
    limit: Optional[int] = typer.Option(
        None, "--limit", "-l", help="Each provider's limit download count"
    ),
    skip_existing: bool = typer.Option(
        True, "--skip-existing/--no-skip-existing", help="Skip existing files"
    ),
) -> None:
    """Backup images from all enabled providers"""
    service: BackupService = app.service
    config: AppConfig = app.config
    verbose: bool = app.verbose

    # Set output directory
    output_dir = output if output else Path(config.default_output_dir)

    # Get all enabled providers
    enabled_providers = [
        name
        for name, provider_config in config.providers.items()
        if provider_config.enabled and provider_config.validate_config()
    ]

    if not enabled_providers:
        typer.echo("❌ No enabled and valid providers")
        raise typer.Exit(code=1)

    typer.echo(f"Will backup the following providers: {', '.join(enabled_providers)}")
    typer.echo(f"Output directory: {output_dir}")

    success_count = 0

    for provider_name in enabled_providers:
        typer.echo(f"\nStarting to backup {provider_name}...")

        success = service.backup_images(
            provider_name=provider_name,
            output_dir=output_dir,
            limit=limit,
            skip_existing=skip_existing,
            verbose=verbose,
        )

        if success:
            success_count += 1
        else:
            typer.echo(f"❌ {provider_name} backup failed")

    typer.echo(
        f"\nBackup completed: {success_count}/{len(enabled_providers)} providers backed up successfully"
    )

    if success_count < len(enabled_providers):
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
