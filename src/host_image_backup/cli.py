from pathlib import Path

import typer
from loguru import logger
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .config import AppConfig
from .service import BackupService

app = typer.Typer(
    name="host-image-backup",
    no_args_is_help=False,
)
console = Console()


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
    ctx: typer.Context = typer.Option(None),  # type: ignore
) -> None:
    setup_logging(verbose)

    # if there is no subcommand, show help
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit(code=0)

    # For init command, we don't need to load configuration
    if ctx.invoked_subcommand == "init":
        return

    # Load configuration for other commands
    app_config = AppConfig.load(config)
    # Create backup service
    backup_service = BackupService(app_config)

    # Store in app context
    app.config = app_config  # type: ignore
    app.service = backup_service  # type: ignore
    app.verbose = verbose  # type: ignore


@app.command()
def init() -> None:
    """Initialize default configuration file"""
    # Check if config file already exists
    config_file = AppConfig.get_config_file()
    if config_file.exists():
        console.print(
            Panel(
                f"[yellow]Configuration file already exists: {config_file}[/yellow]",
                title="Warning",
                border_style="yellow",
            )
        )
        # Ask user if they want to overwrite
        confirm = typer.confirm("Do you want to overwrite the existing configuration?")
        if not confirm:
            console.print("[blue]Operation cancelled.[/blue]")
            raise typer.Exit(code=0)

    # Create default configuration
    config = AppConfig()
    config.create_default_config()

    console.print(
        Panel(
            f"[green]Configuration file created: {config_file}[/green]\n"
            "[yellow]Please edit the configuration file and add your image hosting configuration information.[/yellow]",
            title="Configuration Created",
            border_style="green",
        )
    )


@app.command()
def backup(
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
) -> None:
    """Backup images from the specified provider"""
    service: BackupService = app.service  # type: ignore
    config: AppConfig = app.config  # type: ignore
    verbose: bool = app.verbose  # type: ignore

    # Check if provider exists
    if provider not in service.list_providers():
        console.print(f"[red]Unknown provider: {provider}[/red]")
        available_providers = ", ".join(service.list_providers())
        console.print(f"[yellow]Available providers: {available_providers}[/yellow]")
        raise typer.Exit(code=1)

    # Set output directory
    output_dir = output if output else Path(config.default_output_dir)

    console.print(
        Panel(
            f"[cyan]Starting to backup images from {provider} to {output_dir}[/cyan]",
            title="Backup Started",
            border_style="blue",
        )
    )

    if limit:
        console.print(f"[blue]Limit download count: {limit}[/blue]")

    if skip_existing:
        console.print("[blue]Skip existing files[/blue]")

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
        console.print("[green]Backup completed successfully[/green]")
    else:
        console.print()  # Add empty line before error message
        console.print("[red]Errors occurred during backup[/red]")
        raise typer.Exit(code=1)


@app.command("backup-all")
def backup_all(
    output: Path | None = typer.Option(None, "--output", "-o", help="Output directory for all providers"),
    limit: int | None = typer.Option(
        None, "--limit", "-l", help="Limit download count per provider"
    ),
    skip_existing: bool = typer.Option(
        True,
        "--skip-existing/--no-skip-existing",
        help="Skip existing files [default: skip-existing]",
    ),
) -> None:
    """Backup images from all enabled providers"""
    service: BackupService = app.service  # type: ignore
    config: AppConfig = app.config  # type: ignore
    verbose: bool = app.verbose  # type: ignore

    # Set output directory
    output_dir = output if output else Path(config.default_output_dir)

    # Get all enabled providers
    enabled_providers = [
        name
        for name, provider_config in config.providers.items()
        if provider_config.enabled and provider_config.validate_config()
    ]

    if not enabled_providers:
        console.print("[red]No enabled and valid providers[/red]")
        raise typer.Exit(code=1)

    providers_list = ", ".join(enabled_providers)
    console.print(
        Panel(
            f"[cyan]Will backup the following providers: {providers_list}[/cyan]\n"
            f"[blue]Output directory: {output_dir}[/blue]",
            title="Backup All Providers",
            border_style="blue",
        )
    )

    success_count = 0

    for provider_name in enabled_providers:
        console.print(
            Panel(
                f"[cyan]Starting to backup {provider_name}...[/cyan]",
                title=f"Provider: {provider_name}",
                border_style="yellow",
            )
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
            console.print(f"[red]{provider_name} backup failed[/red]")

    result_text = Text(
        f"\nBackup completed: {success_count}/{len(enabled_providers)} providers backed up successfully",
        style="green" if success_count == len(enabled_providers) else "yellow",
    )
    console.print(result_text)

    if success_count < len(enabled_providers):
        raise typer.Exit(code=1)


@app.command("list")
def list_providers() -> None:
    """List all available providers"""
    service: BackupService = app.service  # type: ignore
    config: AppConfig = app.config  # type: ignore

    providers = service.list_providers()

    table = Table(
        title="Available Providers", show_header=True, header_style="bold magenta"
    )
    table.add_column("Status", style="bold", width=12)
    table.add_column("Provider Name")

    for provider_name in providers:
        status = (
            "[green]Enabled[/green]"
            if provider_name in config.providers
            and config.providers[provider_name].enabled
            else "[red]Disabled[/red]"
        )
        table.add_row(status, provider_name)

    console.print(table)


@app.command()
def test(provider: str = typer.Argument(..., help="Provider name")) -> None:
    """Test connection to the specified provider"""
    service: BackupService = app.service  # type: ignore

    if provider not in service.list_providers():
        console.print(f"[red]Unknown provider: {provider}[/red]")
        raise typer.Exit(code=1)

    console.print(f"[cyan]Testing {provider} connection...[/cyan]")
    success = service.test_provider(provider)

    if success:
        console.print("[green]Connection test passed[/green]")
    else:
        console.print("[red]Connection test failed[/red]")
        raise typer.Exit(code=1)


@app.command()
def info(provider: str = typer.Argument(..., help="Provider name")) -> None:
    """Show detailed information for the specified provider"""
    service: BackupService = app.service  # type: ignore

    if provider not in service.list_providers():
        console.print(f"[red]Unknown provider: {provider}[/red]")
        raise typer.Exit(code=1)

    service.show_provider_info(provider)


@app.command()
def upload(
    provider: str = typer.Argument(..., help="Provider name"),
    file: Path = typer.Argument(
        ..., help="File path to upload", exists=True, file_okay=True
    ),
    remote_path: str | None = typer.Option(
        None, "--remote-path", "-r", help="Remote path for the file"
    ),
) -> None:
    """Upload a single image to the specified provider"""
    service: BackupService = app.service  # type: ignore
    verbose: bool = app.verbose  # type: ignore

    # Check if provider exists
    if provider not in service.list_providers():
        console.print(f"[red]Unknown provider: {provider}[/red]")
        available_providers = ", ".join(service.list_providers())
        console.print(f"[yellow]Available providers: {available_providers}[/yellow]")
        raise typer.Exit(code=1)

    console.print(
        Panel(
            f"[cyan]Uploading {file.name} to {provider}[/cyan]",
            title="Upload",
            border_style="blue",
        )
    )

    if remote_path:
        console.print(f"[blue]Remote path: {remote_path}[/blue]")

    # Execute upload
    success = service.upload_image(
        provider_name=provider,
        file_path=file,
        remote_path=remote_path,
        verbose=verbose,
    )

    if success:
        console.print("[green]Upload completed successfully[/green]")
    else:
        console.print("[red]Upload failed[/red]")
        raise typer.Exit(code=1)


@app.command("upload-all")
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
) -> None:
    """Upload multiple images from a directory to the specified provider"""
    service: BackupService = app.service  # type: ignore
    verbose: bool = app.verbose  # type: ignore

    # Check if provider exists
    if provider not in service.list_providers():
        console.print(f"[red]Unknown provider: {provider}[/red]")
        available_providers = ", ".join(service.list_providers())
        console.print(f"[yellow]Available providers: {available_providers}[/yellow]")
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
        console.print(
            f"[yellow]No image files found matching pattern: {pattern}[/yellow]"
        )
        raise typer.Exit(code=1)

    console.print(
        Panel(
            f"[cyan]Uploading {len(files_to_upload)} images from {directory} to {provider}[/cyan]\n"
            f"[blue]Pattern: {pattern}[/blue]\n"
            f"[blue]Remote prefix: {remote_prefix or 'None'}[/blue]",
            title="Batch Upload",
            border_style="blue",
        )
    )

    # Execute batch upload
    success = service.upload_batch(
        provider_name=provider,
        file_paths=files_to_upload,
        remote_prefix=remote_prefix,
        verbose=verbose,
    )

    if success:
        console.print("[green]Batch upload completed successfully[/green]")
    else:
        console.print("[red]Some uploads failed[/red]")
        raise typer.Exit(code=1)


@app.command()
def stats(
    detailed: bool = typer.Option(
        False, "--detailed", "-d", help="Show detailed statistics by operation type"
    ),
) -> None:
    """Show backup statistics and summary information"""
    service: BackupService = app.service  # type: ignore

    stats = service.metadata_manager.get_statistics()

    table = Table(
        title="[bold]Backup Statistics[/bold]",
        show_header=True,
        header_style="bold blue",
    )
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Total Operations", str(stats["total_operations"]))
    table.add_row("Successful Operations", str(stats["successful_operations"]))
    table.add_row("Failed Operations", str(stats["failed_operations"]))
    table.add_row("Total Files", str(stats["total_files"]))
    table.add_row("Total Size", f"{stats['total_size']:,} bytes")

    console.print(table)

    # Show operations by type if detailed flag is set
    if detailed and stats["operations_by_type"]:
        console.print()
        console.print("[bold]Operations by Type:[/bold]")
        for op_type, count in stats["operations_by_type"].items():
            console.print(f"  {op_type}: {count}")


@app.command()
def history(
    provider: str | None = typer.Option(
        None, "--provider", "-p", help="Filter results by provider"
    ),
    limit: int | None = typer.Option(
        None, "--limit", "-l", help="Limit number of records to show"
    ),
) -> None:
    """Show backup operation history records"""
    service: BackupService = app.service  # type: ignore

    records = service.metadata_manager.get_backup_records(
        operation=None,
        provider=provider,
        limit=limit,
    )

    if not records:
        console.print("[yellow]No backup records found[/yellow]")
        return

    table = Table(
        title="[bold]Recent Backup Records[/bold]",
        show_header=True,
        header_style="bold blue",
    )
    table.add_column("Time", style="cyan")
    table.add_column("Operation", style="magenta")
    table.add_column("Provider", style="green")
    table.add_column("File", style="yellow")
    table.add_column("Status", style="red")

    for record in records[:20]:  # Show last 20 records
        status_color = "green" if record.status == "success" else "red"
        table.add_row(
            record.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if record.created_at
            else "Unknown",
            record.operation,
            record.provider,
            Path(record.file_path).name,
            f"[{status_color}]{record.status}[/{status_color}]",
        )

    console.print(table)


@app.command()
def tool(
    action: str = typer.Argument(..., help="Tool action: duplicates, cleanup, verify, compress"),
) -> None:
    """Utility tools for backup management"""
    service: BackupService = app.service  # type: ignore

    if action == "duplicates":
        duplicates = service.metadata_manager.find_duplicates()

        if not duplicates:
            console.print("[green]No duplicate files found[/green]")
            return

        table = Table(
            title="[bold]Duplicate Files[/bold]",
            show_header=True,
            header_style="bold blue",
        )
        table.add_column("Hash", style="cyan")
        table.add_column("Files", style="magenta")

        for file_hash, files in list(duplicates.items())[
            :10
        ]:  # Show first 10 duplicates
            file_names = [Path(f).name for f in files]
            table.add_row(file_hash[:8] + "...", "\n".join(file_names))

        console.print(table)

    elif action == "cleanup":
        # TODO: Implement cleanup functionality
        console.print("[yellow]Cleanup functionality not yet implemented[/yellow]")

    elif action == "verify":
        # TODO: Implement verification functionality
        console.print("[yellow]Verification functionality not yet implemented[/yellow]")

    elif action == "compress":
        # This will be handled by the compress command below
        console.print("[yellow]Please use 'hib compress' command with options[/yellow]")

    else:
        console.print(f"[red]Unknown tool action: {action}[/red]")
        console.print("[yellow]Available actions: duplicates, cleanup, verify, compress[/yellow]")
        raise typer.Exit(code=1)


@app.command()
def compress(
    input_path: Path = typer.Argument(
        ...,
        help="File or directory to compress",
        exists=True
    ),
    quality: int = typer.Option(
        85,
        "--quality",
        "-q",
        help="Compression quality (1-100)",
        min=1,
        max=100
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for compressed files"
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        "-r",
        help="Recursively compress images in subdirectories"
    ),
    format: str = typer.Option(
        None,
        "--format",
        "-f",
        help="Output format (JPEG, PNG, WEBP)"
    ),
    skip_existing: bool = typer.Option(
        True,
        "--skip-existing/--overwrite-existing",
        help="Skip files that already exist in output directory"
    ),
) -> None:
    """Compress images with high fidelity"""
    service: BackupService = app.service  # type: ignore
    verbose: bool = app.verbose  # type: ignore

    # Validate format if provided
    if format and format.upper() not in ["JPEG", "PNG", "WEBP"]:
        console.print("[red]Invalid format. Supported formats: JPEG, PNG, WEBP[/red]")
        raise typer.Exit(code=1)

    # Set default output directory if not provided
    if output is None:
        if input_path.is_file():
            output = input_path.parent / "compressed"
        else:
            output = input_path / "compressed"

    console.print(
        Panel(
            f"[cyan]Starting image compression[/cyan]\n"
            f"[blue]Input: {input_path}[/blue]\n"
            f"[blue]Output: {output}[/blue]\n"
            f"[blue]Quality: {quality}%[/blue]\n"
            f"[blue]Format: {format or 'Same as input'}[/blue]",
            title="Image Compression",
            border_style="blue",
        )
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
        console.print("[green]Compression completed successfully[/green]")
    else:
        console.print("[red]Compression failed[/red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
