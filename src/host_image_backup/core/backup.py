import concurrent.futures
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger
from rich.console import Console

from ..providers.base import BaseProvider, ImageInfo
from ..utils.file_utils import FileUtils
from ..utils.metadata import MetadataManager


@dataclass
class BackupResult:
    """Backup operation result.

    Parameters
    ----------
    success_count : int
        Number of successful downloads.
    error_count : int
        Number of failed downloads.
    skip_count : int
        Number of skipped downloads.
    total_files : int
        Total number of files processed.
    provider_name : str
        Name of the provider.
    """

    success_count: int
    error_count: int
    skip_count: int
    total_files: int
    provider_name: str


class BackupExecutor:
    """Backup executor for Host Image Backup.

    This class handles the execution of backup operations including
    concurrent downloading, retry logic, and progress tracking.

    Parameters
    ----------
    provider_manager : Any
        Provider manager instance.
    config_manager : Any
        Configuration manager instance.
    metadata_manager : MetadataManager
        Metadata manager instance.
    """

    def __init__(
        self,
        provider_manager: Any,
        config_manager: Any,
        metadata_manager: MetadataManager,
    ):
        """Initialize backup executor."""
        self._provider_manager = provider_manager
        self._config_manager = config_manager
        self._metadata_manager = metadata_manager
        self._console = Console()
        self._logger = logger

    def backup_images(
        self,
        provider_name: str,
        output_dir: Path,
        limit: int | None = None,
        skip_existing: bool = True,
        verbose: bool = False,
    ) -> BackupResult:
        """Execute backup operation for a provider.

        Parameters
        ----------
        provider_name : str
            Name of the provider to backup from.
        output_dir : Path
            Output directory for backed up images.
        limit : int, optional
            Maximum number of images to backup.
        skip_existing : bool, default=True
            Skip files that already exist.
        verbose : bool, default=False
            Enable verbose logging.

        Returns
        -------
        BackupResult
            Backup operation result.

        Raises
        ------
        Exception
            If backup operation fails.
        """
        provider = self._provider_manager.get_provider(provider_name)
        if not provider:
            raise ValueError(f"Provider not available: {provider_name}")

        try:
            # Create output directory
            output_dir = Path(output_dir)
            provider_dir = output_dir / provider_name
            FileUtils.ensure_directory_exists(provider_dir)

            # Get total number of images
            total_count = provider.get_image_count()
            if limit and total_count:
                total_count = min(total_count, limit)

            # If we couldn't get the count, set it to None for indefinite progress bar
            if total_count == 0:
                total_count = None

            # Initialize counters
            success_count = 0
            error_count = 0
            skip_count = 0

            # Execute backup with progress tracking
            with self._create_progress_bar() as progress:
                backup_task = progress.add_task(
                    f"Backing up {provider_name}",
                    total=total_count,
                )

                # Process images concurrently
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=self._config_manager.config.max_concurrent_downloads
                ) as executor:
                    # Submit download tasks
                    download_tasks = []
                    for image_info in provider.list_images(limit=limit):
                        output_file = provider_dir / FileUtils.sanitize_filename(
                            image_info.filename
                        )

                        # Skip if file exists and skip_existing is True
                        if skip_existing and output_file.exists():
                            skip_count += 1
                            self._record_skipped_backup(
                                provider_name, output_file, image_info
                            )
                            progress.update(backup_task, advance=1)
                            if verbose:
                                self._console.print(
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
                        download_tasks.append((future, image_info, output_file))

                    # Process completed downloads
                    for future, image_info, output_file in download_tasks:
                        try:
                            result = future.result()
                            if result:
                                success_count += 1
                                self._record_successful_backup(
                                    provider_name, output_file, image_info
                                )
                            else:
                                error_count += 1
                                self._record_failed_backup(
                                    provider_name,
                                    output_file,
                                    image_info,
                                    "Download failed",
                                )
                        except Exception as e:
                            error_count += 1
                            self._record_failed_backup(
                                provider_name,
                                output_file,
                                image_info,
                                f"Download exception: {str(e)}",
                            )
                            if verbose:
                                self._logger.error(f"Download task error: {e}")

                        progress.update(backup_task, advance=1)

            # Show backup summary
            self._show_backup_summary(
                provider_name, success_count, error_count, skip_count
            )

            return BackupResult(
                success_count=success_count,
                error_count=error_count,
                skip_count=skip_count,
                total_files=success_count + error_count + skip_count,
                provider_name=provider_name,
            )

        except Exception as e:
            self._logger.error(f"Backup process error: {e}")
            raise

    def _download_image_with_retry(
        self,
        provider: BaseProvider,
        image_info: ImageInfo,
        output_file: Path,
        verbose: bool,
    ) -> bool:
        """Download image with retry logic.

        Parameters
        ----------
        provider : BaseProvider
            Provider instance.
        image_info : ImageInfo
            Image information.
        output_file : Path
            Output file path.
        verbose : bool
            Enable verbose logging.

        Returns
        -------
        bool
            True if download successful, False otherwise.
        """
        config = self._config_manager.config

        for attempt in range(config.retry_count + 1):
            try:
                result = provider.download_image(image_info, output_file)
                if result:
                    if verbose:
                        self._console.print(
                            f"[green]Download successful: {image_info.filename}[/green]"
                        )
                    return True
                else:
                    if verbose:
                        self._console.print(
                            f"[red]Download failed: {image_info.filename} (attempt {attempt + 1}/{config.retry_count + 1})[/red]"
                        )
            except Exception as e:
                if verbose:
                    self._console.print(
                        f"[red]Download exception: {image_info.filename} (attempt {attempt + 1}/{config.retry_count + 1}): {e}[/red]"
                    )

        return False

    def _record_skipped_backup(
        self, provider_name: str, output_file: Path, image_info: ImageInfo
    ) -> None:
        """Record skipped backup operation in metadata.

        Parameters
        ----------
        provider_name : str
            Provider name.
        output_file : Path
            Output file path.
        image_info : ImageInfo
            Image information.
        """
        self._metadata_manager.record_backup(
            operation="download",
            provider=provider_name,
            file_path=output_file,
            remote_path=image_info.url or image_info.filename,
            file_hash="",
            file_size=0,
            status="skipped",
            message="File already exists and skip_existing is True",
        )

    def _record_successful_backup(
        self, provider_name: str, output_file: Path, image_info: ImageInfo
    ) -> None:
        """Record successful backup operation in metadata.

        Parameters
        ----------
        provider_name : str
            Provider name.
        output_file : Path
            Output file path.
        image_info : ImageInfo
            Image information.
        """
        try:
            file_hash = (
                FileUtils.calculate_file_hash(output_file)
                if output_file.exists()
                else ""
            )
            file_size = (
                FileUtils.get_file_size(output_file) if output_file.exists() else 0
            )

            # Record backup operation
            self._metadata_manager.record_backup(
                operation="download",
                provider=provider_name,
                file_path=output_file,
                remote_path=image_info.url or image_info.filename,
                file_hash=file_hash,
                file_size=file_size,
                status="success",
                message="Download completed successfully",
            )

            # Update image metadata
            if output_file.exists():
                self._update_image_metadata(output_file, file_hash, file_size)

        except Exception as e:
            self._logger.warning(
                f"Failed to record backup metadata for {output_file}: {e}"
            )

    def _record_failed_backup(
        self, provider_name: str, output_file: Path, image_info: ImageInfo, message: str
    ) -> None:
        """Record failed backup operation in metadata.

        Parameters
        ----------
        provider_name : str
            Provider name.
        output_file : Path
            Output file path.
        image_info : ImageInfo
            Image information.
        message : str
            Error message.
        """
        self._metadata_manager.record_backup(
            operation="download",
            provider=provider_name,
            file_path=output_file,
            remote_path=image_info.url or image_info.filename,
            file_hash="",
            file_size=0,
            status="failed",
            message=message,
        )

    def _update_image_metadata(
        self, output_file: Path, file_hash: str, file_size: int
    ) -> None:
        """Update image metadata with dimensions and format.

        Parameters
        ----------
        output_file : Path
            Output file path.
        file_hash : str
            File hash.
        file_size : int
            File size.
        """
        try:
            # Try to get image dimensions
            width = None
            height = None
            format = None

            try:
                from PIL import Image

                with Image.open(output_file) as img:
                    width, height = img.size
                    format = img.format
            except Exception:
                # PIL not available or image processing failed
                pass

            # Update metadata
            self._metadata_manager.update_file_metadata(
                file_path=output_file,
                file_hash=file_hash,
                file_size=file_size,
                width=width,
                height=height,
                format=format,
            )
        except Exception as e:
            self._logger.warning(
                f"Failed to update image metadata for {output_file}: {e}"
            )

    def _create_progress_bar(self):
        """Create progress bar with consistent styling.

        Returns
        -------
        Progress
            Rich progress bar context manager.
        """
        from ..config.styles import create_backup_progress_bar

        return create_backup_progress_bar()

    def _show_backup_summary(
        self, provider_name: str, success: int, error: int, skip: int
    ) -> None:
        """Show backup summary.

        Parameters
        ----------
        provider_name : str
            Provider name.
        success : int
            Number of successful downloads.
        error : int
            Number of failed downloads.
        skip : int
            Number of skipped downloads.
        """
        from ..config.styles import print_backup_summary

        print_backup_summary(provider_name, success, error, skip)

    def validate_backup_requirements(
        self, provider_name: str, output_dir: Path
    ) -> bool:
        """Validate backup requirements.

        Parameters
        ----------
        provider_name : str
            Provider name.
        output_dir : Path
            Output directory.

        Returns
        -------
        bool
            True if requirements are met, False otherwise.
        """
        # Check if provider is available
        if not self._provider_manager.get_provider(provider_name):
            self._console.print(f"[red]Provider not available: {provider_name}[/red]")
            return False

        # Check if output directory is writable
        try:
            FileUtils.ensure_directory_exists(output_dir)
            test_file = output_dir / ".test_write"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            self._console.print(f"[red]Output directory not writable: {e}[/red]")
            return False

        return True

    def estimate_backup_time(
        self, provider_name: str, limit: int | None = None
    ) -> int | None:
        """Estimate backup time in seconds.

        Parameters
        ----------
        provider_name : str
            Provider name.
        limit : int, optional
            Maximum number of images to backup.

        Returns
        -------
        int or None
            Estimated time in seconds, or None if cannot estimate.
        """
        provider = self._provider_manager.get_provider(provider_name)
        if not provider:
            return None

        try:
            # Get image count
            total_count = provider.get_image_count()
            if limit and total_count:
                total_count = min(total_count, limit)

            if not total_count:
                return None

            # Estimate based on average download time and concurrency
            avg_download_time = 5  # seconds per image (conservative estimate)
            max_concurrent = self._config_manager.config.max_concurrent_downloads

            # Calculate estimated time
            estimated_time = (total_count * avg_download_time) / max_concurrent

            return int(estimated_time)
        except Exception:
            return None

    def get_backup_statistics(self, provider_name: str) -> dict[str, Any]:
        """Get backup statistics for a provider.

        Parameters
        ----------
        provider_name : str
            Provider name.

        Returns
        -------
        Dict[str, Any]
            Backup statistics.
        """
        provider = self._provider_manager.get_provider(provider_name)
        if not provider:
            return {}

        try:
            # Get provider statistics
            image_count = provider.get_image_count()

            # Get backup records from metadata
            backup_records = self._metadata_manager.get_backup_records(
                operation="download",
                provider=provider_name,
            )

            # Calculate statistics
            total_backups = len(backup_records)
            successful_backups = sum(1 for r in backup_records if r.status == "success")
            failed_backups = sum(1 for r in backup_records if r.status == "failed")

            # Calculate total size
            total_size = sum(
                r.file_size for r in backup_records if r.status == "success"
            )

            return {
                "provider_name": provider_name,
                "total_images": image_count,
                "total_backups": total_backups,
                "successful_backups": successful_backups,
                "failed_backups": failed_backups,
                "success_rate": (successful_backups / total_backups * 100)
                if total_backups > 0
                else 0,
                "total_size": total_size,
                "formatted_size": FileUtils.format_file_size(total_size),
            }
        except Exception as e:
            self._logger.error(
                f"Failed to get backup statistics for {provider_name}: {e}"
            )
            return {}
