from pathlib import Path

import typer
from loguru import logger
from rich import print

from .config.config_models import AppConfig
from .config.styles import (
    console,
    print_duplicates,
    print_error,
    print_header,
    print_history,
    print_info,
    print_provider_list,
    print_section,
    print_statistics,
    print_success,
    print_warning,
)
from .core.service import BackupService

app = typer.Typer(
    name="host-image-backup",
    no_args_is_help=False,
)

# Create sub-apps for command groups
config_app = typer.Typer(
    name="config",
    help="Configuration management commands",
    no_args_is_help=False,
)
app.add_typer(config_app)

provider_app = typer.Typer(
    name="provider",
    help="Provider management commands",
    no_args_is_help=False,
)
app.add_typer(provider_app)

backup_app = typer.Typer(
    name="backup",
    help="Backup management commands",
    no_args_is_help=False,
)
app.add_typer(backup_app)

upload_app = typer.Typer(
    name="upload",
    help="Upload management commands",
    no_args_is_help=False,
)
app.add_typer(upload_app)

data_app = typer.Typer(
    name="data",
    help="Data management commands",
    no_args_is_help=False,
)
app.add_typer(data_app)


def setup_logging(verbose: bool = False) -> None:
    """Setup logging

    Parameters
    ----------
    verbose : bool, default=False
        Whether to enable verbose logging.
    """
    level = "DEBUG" if verbose else "INFO"
    logger.remove()  # Remove default logger

    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    logger.add(
        "logs/host_image_backup_{time}.log",
        rotation="5 MB",
        retention="1 week",
        compression="zip",
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    )
    if verbose:
        logger.add(
            lambda msg: print(msg, end=""),
            level=level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        )


@app.callback(invoke_without_command=True)
def main(
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        exists=True,
        help="Configuration file path [default: ~/.config/host-image-backup/config.yaml]",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed logs"),
    ctx: typer.Context = typer.Option(None),
) -> None:
    setup_logging(verbose)

    # if there is no subcommand, show help
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit(code=0)

    # For config init command, we don't need to load configuration
    if ctx.invoked_subcommand == "config" and ctx.args and ctx.args[0] == "init":
        return

    # Load configuration for other commands
    app_config = AppConfig.load(config)
    # Create backup service
    backup_service = BackupService(app_config)

    # Store in context object
    ctx.obj = {
        "config": app_config,
        "service": backup_service,
        "verbose": verbose,
    }


@config_app.command("init")
def config_init() -> None:
    """Initialize default configuration file"""
    # Check if config file already exists
    config_file = AppConfig.get_config_file()
    if config_file.exists():
        print_warning(f"Configuration file already exists: {config_file}")
        # Ask user if they want to overwrite
        confirm = typer.confirm("Do you want to overwrite the existing configuration?")
        if not confirm:
            print_info("Operation cancelled.")
            raise typer.Exit(code=0)

    # Create default configuration
    config = AppConfig()
    config.create_default_config()

    print_success(f"Configuration file created: {config_file}")
    print_warning(
        "Please edit the configuration file and add your image hosting configuration information."
    )


@backup_app.command("start")
def backup_start(
    provider: str = typer.Argument(..., help="Provider name"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output directory"),
    limit: int | None = typer.Option(
        None, "--limit", "-l", help="Limit download count"
    ),
    skip_existing: bool = typer.Option(
        True,
        "--skip-existing/--no-skip-existing",
        help="Skip existing files [default: skip-existing]",
    ),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """Backup images from the specified provider"""
    service: BackupService = ctx.obj["service"]
    config: AppConfig = ctx.obj["config"]
    verbose: bool = ctx.obj["verbose"]

    # Check if provider exists
    if provider not in service.list_providers():
        print_error(f"Unknown provider: {provider}")
        available_providers = ", ".join(service.list_providers())
        print_warning(f"Available providers: {available_providers}")
        raise typer.Exit(code=1)

    # Set output directory
    output_dir = output if output else Path(config.default_output_dir)

    print_section(
        "Backup Started", f"Starting to backup images from {provider} to {output_dir}"
    )

    if limit:
        print_info(f"Limit download count: {limit}")

    if skip_existing:
        print_info("Skip existing files")

    # Execute backup
    success = service.backup_images(
        provider_name=provider,
        output_dir=output_dir,
        limit=limit,
        skip_existing=skip_existing,
        verbose=verbose,
    )

    if success:
        console.print()  # Add empty line before success message
        print_success("Backup completed successfully")
    else:
        console.print()  # Add empty line before error message
        print_error("Errors occurred during backup")
        raise typer.Exit(code=1)


def _backup_all_impl(
    output: Path | None,
    limit: int | None,
    skip_existing: bool,
    ctx: typer.Context,
) -> None:
    """Backup images from all enabled providers (shared implementation)"""
    service: BackupService = ctx.obj["service"]
    config: AppConfig = ctx.obj["config"]
    verbose: bool = ctx.obj["verbose"]

    output_dir = output if output else Path(config.default_output_dir)
    enabled_providers = [
        name
        for name, provider_config in config.providers.items()
        if provider_config.enabled and provider_config.validate_config()
    ]

    if not enabled_providers:
        print_error("No enabled and valid providers")
        raise typer.Exit(code=1)

    providers_list = ", ".join(enabled_providers)
    print_section(
        "Backup All Providers",
        f"Will backup the following providers: {providers_list}\nOutput directory: {output_dir}",
    )

    success_count = 0

    for provider_name in enabled_providers:
        print_section(
            f"Provider: {provider_name}", f"Starting to backup {provider_name}..."
        )

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
            print_error(f"{provider_name} backup failed")

    console.print()  # Add empty line before result
    if success_count == len(enabled_providers):
        print_success(
            f"Backup completed: {success_count}/{len(enabled_providers)} providers backed up successfully"
        )
    else:
        print_warning(
            f"Backup completed: {success_count}/{len(enabled_providers)} providers backed up successfully"
        )

    if success_count < len(enabled_providers):
        raise typer.Exit(code=1)


@backup_app.command("all")
def backup_all(
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output directory for all providers"
    ),
    limit: int | None = typer.Option(
        None, "--limit", "-l", help="Limit download count per provider"
    ),
    skip_existing: bool = typer.Option(
        True,
        "--skip-existing/--no-skip-existing",
        help="Skip existing files [default: skip-existing]",
    ),
    ctx: typer.Context = typer.Option(None),
) -> None:
    _backup_all_impl(output, limit, skip_existing, ctx)


@app.command("backup-all")
def backup_all_cli(
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output directory for all providers"
    ),
    limit: int | None = typer.Option(
        None, "--limit", "-l", help="Limit download count per provider"
    ),
    skip_existing: bool = typer.Option(
        True,
        "--skip-existing/--no-skip-existing",
        help="Skip existing files [default: skip-existing]",
    ),
    ctx: typer.Context = typer.Option(None),
) -> None:
    _backup_all_impl(output, limit, skip_existing, ctx)


@provider_app.command("list")
def provider_list(ctx: typer.Context = typer.Option(None)) -> None:
    """List all available providers"""
    service: BackupService = ctx.obj["service"]
    config: AppConfig = ctx.obj["config"]

    providers = service.list_providers()

    provider_statuses = []
    for provider_name in providers:
        status = (
            "Enabled"
            if provider_name in config.providers
            and config.providers[provider_name].enabled
            else "Disabled"
        )
        provider_statuses.append((status, provider_name))

    print_provider_list(provider_statuses)


@provider_app.command("test")
def provider_test(
    provider: str = typer.Argument(..., help="Provider name"),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """Test connection to the specified provider"""
    service: BackupService = ctx.obj["service"]

    if provider not in service.list_providers():
        print_error(f"Unknown provider: {provider}")
        raise typer.Exit(code=1)

    print_info(f"Testing {provider} connection...")
    success = service.test_provider(provider)

    if success:
        print_success("Connection test passed")
    else:
        print_error("Connection test failed")
        raise typer.Exit(code=1)


@provider_app.command("info")
def provider_info(
    provider: str = typer.Argument(..., help="Provider name"),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """Show detailed information for the specified provider"""
    service: BackupService = ctx.obj["service"]

    if provider not in service.list_providers():
        print_error(f"Unknown provider: {provider}")
        raise typer.Exit(code=1)

    service.show_provider_info(provider)


@upload_app.command("file")
def upload(
    provider: str = typer.Argument(..., help="Provider name"),
    file: Path = typer.Argument(
        ..., help="File path to upload", exists=True, file_okay=True
    ),
    remote_path: str | None = typer.Option(
        None, "--remote-path", "-r", help="Remote path for the file"
    ),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """Upload a single image to the specified provider"""
    service: BackupService = ctx.obj["service"]
    verbose: bool = ctx.obj["verbose"]

    # Check if provider exists
    if provider not in service.list_providers():
        print_error(f"Unknown provider: {provider}")
        available_providers = ", ".join(service.list_providers())
        print_warning(f"Available providers: {available_providers}")
        raise typer.Exit(code=1)

    print_section("Upload", f"Uploading {file.name} to {provider}")

    if remote_path:
        print_info(f"Remote path: {remote_path}")

    # Execute upload
    success = service.upload_image(
        provider_name=provider,
        file_path=file,
        remote_path=remote_path,
        verbose=verbose,
    )

    if success:
        print_success("Upload completed successfully")
    else:
        print_error("Upload failed")
        raise typer.Exit(code=1)


@upload_app.command("directory")
def upload_all(
    provider: str = typer.Argument(..., help="Provider name"),
    directory: Path = typer.Argument(
        ...,
        help="Directory containing images to upload",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    pattern: str = typer.Option(
        "*", "--pattern", "-p", help="File pattern to match (default: *)"
    ),
    remote_prefix: str | None = typer.Option(
        None, "--remote-prefix", "-r", help="Remote prefix for all files"
    ),
    limit: int | None = typer.Option(
        None, "--limit", "-l", help="Limit number of files to upload"
    ),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """Upload multiple images from a directory to the specified provider"""
    service: BackupService = ctx.obj["service"]
    verbose: bool = ctx.obj["verbose"]

    # Check if provider exists
    if provider not in service.list_providers():
        print_error(f"Unknown provider: {provider}")
        available_providers = ", ".join(service.list_providers())
        print_warning(f"Available providers: {available_providers}")
        raise typer.Exit(code=1)

    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".webp",
        ".svg",
        ".tiff",
        ".tif",
        ".ico",
    }

    pattern_with_ext = f"{pattern}*"
    if not any(pattern.lower().endswith(ext) for ext in image_extensions):
        # Add all image extensions if pattern doesn't specify extension
        files_to_upload = []
        for ext in image_extensions:
            files_to_upload.extend(directory.glob(f"{pattern}*{ext}"))
    else:
        files_to_upload = list(directory.glob(pattern_with_ext))

    # Filter only existing image files
    files_to_upload = [
        f
        for f in files_to_upload
        if f.is_file() and f.suffix.lower() in image_extensions
    ]

    if limit:
        files_to_upload = files_to_upload[:limit]

    if not files_to_upload:
        print_warning(f"No image files found matching pattern: {pattern}")
        raise typer.Exit(code=1)

    print_section(
        "Batch Upload",
        f"Uploading {len(files_to_upload)} images from {directory} to {provider}\nPattern: {pattern}\nRemote prefix: {remote_prefix or 'None'}",
    )

    # Execute batch upload
    success = service.upload_batch(
        provider_name=provider,
        file_paths=files_to_upload,
        remote_prefix=remote_prefix,
        verbose=verbose,
    )

    if success:
        print_success("Batch upload completed successfully")
    else:
        print_error("Some uploads failed")
        raise typer.Exit(code=1)


@data_app.command("stats")
def stats(
    detailed: bool = typer.Option(
        False, "--detailed", "-d", help="Show detailed statistics by operation type"
    ),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """Show backup statistics and summary information"""
    service: BackupService = ctx.obj["service"]

    stats = service.metadata_manager.get_statistics()
    print_statistics(stats)

    # Show operations by type if detailed flag is set
    if detailed and stats["operations_by_type"]:
        console.print()
        print_header("Operations by Type:")
        for op_type, count in stats["operations_by_type"].items():
            console.print(f"  {op_type}: {count}")


@data_app.command("history")
def history(
    provider: str | None = typer.Option(
        None, "--provider", "-p", help="Filter results by provider"
    ),
    limit: int | None = typer.Option(
        None, "--limit", "-l", help="Limit number of records to show"
    ),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """Show backup operation history records"""
    service: BackupService = ctx.obj["service"]

    records = service.metadata_manager.get_backup_records(
        operation=None,
        provider=provider,
        limit=limit,
    )

    print_history(records)


@data_app.command("duplicates")
def duplicates(ctx: typer.Context = typer.Option(None)) -> None:
    """Find and display duplicate files"""
    service: BackupService = ctx.obj["service"]

    duplicates = service.metadata_manager.find_duplicates()
    print_duplicates(duplicates)


@data_app.command("cleanup")
def cleanup() -> None:
    """Clean up backup files and metadata"""
    print_warning("Cleanup functionality not yet implemented")


@data_app.command("verify")
def verify() -> None:
    """Verify backup file integrity"""
    print_warning("Verification functionality not yet implemented")


@data_app.command("compress")
def compress(
    input_path: Path = typer.Argument(
        ..., help="File or directory to compress", exists=True
    ),
    quality: int = typer.Option(
        85, "--quality", "-q", help="Compression quality (1-100)", min=1, max=100
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output directory for compressed files"
    ),
    recursive: bool = typer.Option(
        False, "--recursive", "-r", help="Recursively compress images in subdirectories"
    ),
    format: str = typer.Option(
        None, "--format", "-f", help="Output format (JPEG, PNG, WEBP)"
    ),
    skip_existing: bool = typer.Option(
        True,
        "--skip-existing/--overwrite-existing",
        help="Skip files that already exist in output directory",
    ),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """Compress images with high fidelity"""
    service: BackupService = ctx.obj["service"]
    verbose: bool = ctx.obj["verbose"]

    # Validate format if provided
    if format and format.upper() not in ["JPEG", "PNG", "WEBP"]:
        print_error("Invalid format. Supported formats: JPEG, PNG, WEBP")
        raise typer.Exit(code=1)

    # Set default output directory if not provided
    if output is None:
        if input_path.is_file():
            output = input_path.parent / "compressed"
        else:
            output = input_path / "compressed"

    print_section(
        "Image Compression",
        f"Starting image compression\nInput: {input_path}\nOutput: {output}\nQuality: {quality}%\nFormat: {format or 'Same as input'}",
    )

    # Execute compression
    success = service.compress_images(
        input_path=input_path,
        output_dir=output,
        quality=quality,
        output_format=format,
        recursive=recursive,
        skip_existing=skip_existing,
        verbose=verbose,
    )

    if success:
        print_success("Compression completed successfully")
    else:
        print_error("Compression failed")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
