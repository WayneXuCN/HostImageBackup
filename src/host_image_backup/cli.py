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
        None, "--config", "-c", exists=True, 
        help="Configuration file path [default: ~/.config/host-image-backup/config.yaml]"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed logs"),
    ctx: typer.Context = typer.Option(...),
) -> None:
    setup_logging(verbose)

    # if there is no arguments, show help
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit(code=0)

    # Load configuration
    app_config = AppConfig.load(config)

    # Create backup service
    backup_service = BackupService(app_config)

    # Store in app context
    app.config = app_config  # type: ignore
    app.service = backup_service  # type: ignore
    app.verbose = verbose  # type: ignore


@app.command()
def init() -> None:
    """Initialize configuration file"""
    config: AppConfig = app.config  # type: ignore

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
        True, "--skip-existing/--no-skip-existing", help="Skip existing files"
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
    """Test provider connection"""
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
    """Show provider detailed information"""
    service: BackupService = app.service  # type: ignore

    if provider not in service.list_providers():
        console.print(f"[red]Unknown provider: {provider}[/red]")
        raise typer.Exit(code=1)

    service.show_provider_info(provider)


@app.command("backup-all")
def backup_all(
    output: Path | None = typer.Option(None, "--output", "-o", help="Output directory"),
    limit: int | None = typer.Option(
        None, "--limit", "-l", help="Each provider's limit download count"
    ),
    skip_existing: bool = typer.Option(
        True, "--skip-existing/--no-skip-existing", help="Skip existing files"
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


if __name__ == "__main__":
    app()
