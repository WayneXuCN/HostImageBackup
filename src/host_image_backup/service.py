import concurrent.futures
from pathlib import Path

from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table

from .config import AppConfig
from .providers import BaseProvider, ImageInfo
from .providers.cos import COSProvider
from .providers.github import GitHubProvider
from .providers.imgur import ImgurProvider
from .providers.oss import OSSProvider
from .providers.sms import SMSProvider


class BackupService:
    """Backup service"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.console = Console()
        self.logger = logger

        # Initialize provider mapping
        self.provider_classes = {
            "oss": OSSProvider,
            "cos": COSProvider,
            "sms": SMSProvider,
            "imgur": ImgurProvider,
            "github": GitHubProvider,
        }

    def get_provider(self, provider_name: str) -> BaseProvider | None:
        """Get provider instance"""
        if provider_name not in self.config.providers:
            self.logger.error(f"Provider configuration not found: {provider_name}")
            return None

        provider_config = self.config.providers[provider_name]

        if not provider_config.enabled:
            self.logger.error(f"Provider not enabled: {provider_name}")
            return None

        if not provider_config.validate_config():
            self.logger.error(f"Invalid provider configuration: {provider_name}")
            return None

        provider_class = self.provider_classes.get(provider_name)
        if not provider_class:
            self.logger.error(f"Provider implementation not found: {provider_name}")
            return None

        return provider_class(provider_config)

    def list_providers(self) -> list[str]:
        """List all available providers"""
        return list(self.provider_classes.keys())

    def test_provider(self, provider_name: str) -> bool:
        """Test provider connection"""
        provider = self.get_provider(provider_name)
        if not provider:
            return False

        try:
            result = provider.test_connection()
            if result:
                self.console.print(
                    f"[green]Provider {provider_name} connection test successful[/green]"
                )
            else:
                self.console.print(
                    f"[red]Provider {provider_name} connection test failed[/red]"
                )
            return result
        except Exception as e:
            self.console.print(
                f"[red]Provider {provider_name} connection test exception: {e}[/red]"
            )
            return False

    def backup_images(
        self,
        provider_name: str,
        output_dir: Path,
        limit: int | None = None,
        skip_existing: bool = True,
        verbose: bool = False,
    ) -> bool:
        """Backup images"""
        provider = self.get_provider(provider_name)
        if not provider:
            return False

        try:
            # Create output directory
            output_dir = Path(output_dir)
            provider_dir = output_dir / provider_name
            provider_dir.mkdir(parents=True, exist_ok=True)

            # Get total number of images (for progress bar)
            total_count = provider.get_image_count()
            if limit and total_count:
                total_count = min(total_count, limit)

            # If we couldn't get the count, set it to None to show an indefinite progress bar
            if total_count == 0:
                total_count = None

            success_count = 0
            error_count = 0
            skip_count = 0

            # Create a custom progress bar with rich
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TextColumn(
                    "[progress.percentage]{task.completed}"
                    + ("/{task.total}" if total_count else "")
                    + " images"
                ),
            ) as progress:
                # If we don't know the total, use an indefinite progress bar
                backup_task = progress.add_task(
                    f"[cyan]Backing up {provider_name}[/cyan]",
                    total=total_count if total_count else None,
                )

                # Create thread pool executor
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=self.config.max_concurrent_downloads
                ) as executor:
                    futures = []

                    for image_info in provider.list_images(limit=limit):
                        # Build output file path
                        output_file = provider_dir / self._sanitize_filename(
                            image_info.filename
                        )

                        # Skip if file exists and skip_existing is True
                        if skip_existing and output_file.exists():
                            skip_count += 1
                            progress.update(backup_task, advance=1)
                            if verbose:
                                self.console.print(
                                    f"[yellow]Skipping existing file: {image_info.filename}[/yellow]"
                                )
                            continue

                        # Submit download task
                        future = executor.submit(
                            self._download_image_with_retry,
                            provider,
                            image_info,
                            output_file,
                            verbose,
                        )
                        futures.append(future)

                    # Wait for all downloads to complete
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
                                self.logger.error(f"Download task error: {e}")

                        progress.update(backup_task, advance=1)

            # Add empty line between progress bar and summary table
            self.console.print()  # Add empty line
            self.console.print()  # Show backup summary
            self._show_backup_summary(
                provider_name, success_count, error_count, skip_count
            )

            return error_count == 0

        except Exception as e:
            self.logger.error(f"Backup process error: {e}")
            return False

    def _download_image_with_retry(
        self,
        provider: BaseProvider,
        image_info: ImageInfo,
        output_file: Path,
        verbose: bool,
    ) -> bool:
        """Download image with retry"""
        for attempt in range(self.config.retry_count + 1):  # +1 for initial attempt
            try:
                result = provider.download_image(image_info, output_file)
                if result:
                    if verbose:
                        self.console.print(
                            f"[green]Download successful: {image_info.filename}[/green]"
                        )
                    return True
                else:
                    if verbose:
                        self.console.print(
                            f"[red]Download failed: {image_info.filename} (attempt {attempt + 1}/{self.config.retry_count + 1})[/red]"
                        )
            except Exception as e:
                if verbose:
                    self.console.print(
                        f"[red]Download exception: {image_info.filename} (attempt {attempt + 1}/{self.config.retry_count + 1}): {e}[/red]"
                    )

        return False

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by removing illegal characters"""
        # Replace illegal characters
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, "_")

        # Limit filename length
        if len(filename) > 255:
            name, ext = Path(filename).stem, Path(filename).suffix
            # Ensure we preserve the extension
            max_name_length = 255 - len(ext)
            if max_name_length > 0:
                filename = name[:max_name_length] + ext
            else:
                # If extension is longer than 255 chars, we have bigger problems
                filename = name[:255]

        return filename

    def _show_backup_summary(
        self, provider_name: str, success: int, error: int, skip: int
    ) -> None:
        """Show backup summary"""
        table = Table(
            title=f"[bold]{provider_name} Backup Summary[/bold]",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Item", style="cyan", no_wrap=True)
        table.add_column("Count", style="magenta")

        table.add_row("Successfully Downloaded", str(success))
        table.add_row("Failed Downloads", str(error))
        table.add_row("Skipped Files", str(skip))
        table.add_row("Total", str(success + error + skip))

        self.console.print(table)

        if error > 0:
            self.console.print()  # Add empty line before warning
            self.console.print(
                Panel(
                    f"[yellow]There are {error} failed downloads, please check network connection or provider configuration[/yellow]",
                    title="[yellow]Warning[/yellow]",
                    border_style="yellow",
                )
            )

    def show_provider_info(self, provider_name: str) -> None:
        """Show provider information"""
        provider = self.get_provider(provider_name)
        if not provider:
            self.console.print(
                f"[red]Cannot get provider: {provider_name}[/red]", style="red"
            )
            return

        # Test connection
        connection_status = (
            "[green]Normal[/green]"
            if provider.test_connection()
            else "[red]Failed[/red]"
        )

        # Get image count
        try:
            image_count = provider.get_image_count()
            count_text = (
                str(image_count) if image_count is not None else "Not available"
            )
        except Exception as e:
            self.logger.error(f"Error getting image count for {provider_name}: {e}")
            count_text = "Failed to get"

        table = Table(
            title=f"[bold]{provider_name.upper()} Provider Information[/bold]",
            show_header=True,
            header_style="bold blue",
        )
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Name", provider_name.upper())
        table.add_row(
            "Status",
            "[green]Enabled[/green]"
            if provider.is_enabled()
            else "[red]Disabled[/red]",
        )
        table.add_row("Connection Test", connection_status)
        table.add_row("Image Count", count_text)
        table.add_row(
            "Configuration Valid",
            "[green]Yes[/green]" if provider.validate_config() else "[red]No[/red]",
        )

        self.console.print(table)
