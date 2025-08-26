"""Upload service module for Host Image Backup.

This module handles upload operations including single file upload
and batch upload with progress tracking.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger
from rich.console import Console
from rich.panel import Panel

from ..utils.file_utils import FileUtils
from ..utils.metadata import MetadataManager


@dataclass
class BatchUploadResult:
    """Batch upload operation result.

    Parameters
    ----------
    success_count : int
        Number of successful uploads.
    error_count : int
        Number of failed uploads.
    total_files : int
        Total number of files processed.
    provider_name : str
        Name of the provider.
    """

    success_count: int
    error_count: int
    total_files: int
    provider_name: str


class UploadService:
    """Upload service for Host Image Backup.

    This class handles upload operations including single file upload
    and batch upload with progress tracking.

    Parameters
    ----------
    provider_manager : Any
        Provider manager instance.
    metadata_manager : MetadataManager
        Metadata manager instance.
    """

    def __init__(self, provider_manager: Any, metadata_manager: MetadataManager):
        """Initialize upload service."""
        self._provider_manager = provider_manager
        self._metadata_manager = metadata_manager
        self._console = Console()
        self._logger = logger

    def upload_image(
        self,
        provider_name: str,
        file_path: Path,
        remote_path: str | None = None,
        verbose: bool = False,
    ) -> bool:
        """Upload a single image to provider.

        Parameters
        ----------
        provider_name : str
            Name of the provider.
        file_path : Path
            Local file path to upload.
        remote_path : str, optional
            Remote path for the file.
        verbose : bool, default=False
            Enable verbose logging.

        Returns
        -------
        bool
            True if upload successful, False otherwise.
        """
        provider = self._provider_manager.get_provider(provider_name)
        if not provider:
            self._console.print(f"[red]Provider not available: {provider_name}[/red]")
            return False

        try:
            # Check if file exists
            if not file_path.exists():
                self._console.print(f"[red]File not found: {file_path}[/red]")
                return False

            # Calculate file hash and size
            file_hash = FileUtils.calculate_file_hash(file_path)
            file_size = FileUtils.get_file_size(file_path)

            # Show upload start message
            self._console.print(
                Panel(
                    f"[cyan]Uploading {file_path.name} to {provider_name}[/cyan]\n"
                    f"[blue]File size: {FileUtils.format_file_size(file_size)}[/blue]",
                    title="Upload Started",
                    border_style="blue",
                )
            )

            # Upload image
            result = provider.upload_image(file_path, remote_path)

            # Record operation in metadata
            if result.success:
                self._record_successful_upload(
                    provider_name, file_path, remote_path, file_hash, file_size, result
                )

                # Show success message
                self._console.print()
                self._console.print("[green]✓ Upload successful![/green]")
                if result.url:
                    self._console.print(f"[blue]URL: {result.url}[/blue]")

                return True
            else:
                # Record failed operation
                self._record_failed_upload(
                    provider_name, file_path, remote_path, file_hash, file_size, result
                )

                self._console.print()
                self._console.print(f"[red]✗ Upload failed: {result.message}[/red]")
                return False

        except Exception as e:
            self._logger.error(f"Upload process error: {e}")
            self._console.print(f"[red]Upload error: {str(e)}[/red]")
            return False

    def upload_batch(
        self,
        provider_name: str,
        file_paths: list[Path],
        remote_prefix: str | None = None,
        verbose: bool = False,
    ) -> BatchUploadResult:
        """Upload multiple images to provider.

        Parameters
        ----------
        provider_name : str
            Name of the provider.
        file_paths : list[Path]
            List of local file paths to upload.
        remote_prefix : str, optional
            Remote prefix for all files.
        verbose : bool, default=False
            Enable verbose logging.

        Returns
        -------
        BatchUploadResult
            Upload operation result.
        """
        provider = self._provider_manager.get_provider(provider_name)
        if not provider:
            raise ValueError(f"Provider not available: {provider_name}")

        total_files = len(file_paths)
        success_count = 0
        error_count = 0

        # Show batch upload start message
        self._console.print(
            Panel(
                f"[cyan]Starting batch upload to {provider_name}[/cyan]\n"
                f"[blue]Total files: {total_files}[/blue]",
                title="Batch Upload",
                border_style="blue",
            )
        )

        # Create progress bar
        with self._create_progress_bar() as progress:
            upload_task = progress.add_task(
                f"Uploading to {provider_name}",
                total=total_files,
            )

            # Process each file
            for file_path in file_paths:
                try:
                    # Determine remote path
                    remote_path = None
                    if remote_prefix:
                        remote_path = f"{remote_prefix}{file_path.name}"

                    # Upload single file
                    if self.upload_image(
                        provider_name, file_path, remote_path, verbose
                    ):
                        success_count += 1
                    else:
                        error_count += 1

                except Exception as e:
                    error_count += 1
                    self._logger.error(f"Batch upload error for {file_path}: {e}")

                progress.update(upload_task, advance=1)

        # Show summary
        self._console.print()
        self._show_upload_summary(
            provider_name, success_count, error_count, total_files
        )

        return BatchUploadResult(
            success_count=success_count,
            error_count=error_count,
            total_files=total_files,
            provider_name=provider_name,
        )

    def validate_upload_requirements(
        self, provider_name: str, file_paths: list[Path]
    ) -> bool:
        """Validate upload requirements.

        Parameters
        ----------
        provider_name : str
            Provider name.
        file_paths : list[Path]
            List of file paths to upload.

        Returns
        -------
        bool
            True if requirements are met, False otherwise.
        """
        # Check if provider is available
        if not self._provider_manager.get_provider(provider_name):
            self._console.print(f"[red]Provider not available: {provider_name}[/red]")
            return False

        # Check if all files exist
        missing_files = []
        for file_path in file_paths:
            if not file_path.exists():
                missing_files.append(str(file_path))

        if missing_files:
            self._console.print("[red]Missing files:[/red]")
            for file_path in missing_files:
                self._console.print(f"[red]  - {file_path}[/red]")
            return False

        # Check if files are images
        non_image_files = []
        for file_path in file_paths:
            if not FileUtils.is_image_file(file_path):
                non_image_files.append(str(file_path))

        if non_image_files:
            self._console.print("[red]Non-image files:[/red]")
            for file_path in non_image_files:
                self._console.print(f"[red]  - {file_path}[/red]")
            return False

        return True

    def estimate_upload_time(self, file_paths: list[Path]) -> int | None:
        """Estimate upload time in seconds.

        Parameters
        ----------
        file_paths : list[Path]
            List of file paths to upload.

        Returns
        -------
        int or None
            Estimated time in seconds, or None if cannot estimate.
        """
        if not file_paths:
            return 0

        try:
            # Calculate total size
            total_size = sum(
                FileUtils.get_file_size(file_path) for file_path in file_paths
            )

            # Estimate based on average upload speed (conservative: 1 MB/s)
            avg_upload_speed = 1024 * 1024  # 1 MB/s in bytes

            estimated_time = total_size / avg_upload_speed

            return int(estimated_time)
        except Exception:
            return None

    def get_upload_statistics(self, provider_name: str) -> dict[str, Any]:
        """Get upload statistics for a provider.

        Parameters
        ----------
        provider_name : str
            Provider name.

        Returns
        -------
        Dict[str, Any]
            Upload statistics.
        """
        try:
            # Get upload records from metadata
            upload_records = self._metadata_manager.get_backup_records(
                operation="upload",
                provider=provider_name,
            )

            # Calculate statistics
            total_uploads = len(upload_records)
            successful_uploads = sum(1 for r in upload_records if r.status == "success")
            failed_uploads = sum(1 for r in upload_records if r.status == "failed")

            # Calculate total size
            total_size = sum(
                r.file_size for r in upload_records if r.status == "success"
            )

            return {
                "provider_name": provider_name,
                "total_uploads": total_uploads,
                "successful_uploads": successful_uploads,
                "failed_uploads": failed_uploads,
                "success_rate": (successful_uploads / total_uploads * 100)
                if total_uploads > 0
                else 0,
                "total_size": total_size,
                "formatted_size": FileUtils.format_file_size(total_size),
            }
        except Exception as e:
            self._logger.error(
                f"Failed to get upload statistics for {provider_name}: {e}"
            )
            return {}

    def prepare_remote_path(
        self, file_path: Path, remote_prefix: str | None = None
    ) -> str:
        """Prepare remote path for upload.

        Parameters
        ----------
        file_path : Path
            Local file path.
        remote_prefix : str, optional
            Remote prefix for the file.

        Returns
        -------
        str
            Remote path.
        """
        if remote_prefix:
            return f"{remote_prefix}{file_path.name}"
        else:
            return file_path.name

    def filter_image_files(self, file_paths: list[Path]) -> list[Path]:
        """Filter list to include only image files.

        Parameters
        ----------
        file_paths : list[Path]
            List of file paths.

        Returns
        -------
        list[Path]
            List of image file paths.
        """
        return [
            file_path for file_path in file_paths if FileUtils.is_image_file(file_path)
        ]

    def _record_successful_upload(
        self,
        provider_name: str,
        file_path: Path,
        remote_path: str | None,
        file_hash: str,
        file_size: int,
        upload_result: Any,
    ) -> None:
        """Record successful upload in metadata.

        Parameters
        ----------
        provider_name : str
            Provider name.
        file_path : Path
            Local file path.
        remote_path : str, optional
            Remote file path.
        file_hash : str
            File hash.
        file_size : int
            File size.
        upload_result : Any
            Upload result from provider.
        """
        self._metadata_manager.record_backup(
            operation="upload",
            provider=provider_name,
            file_path=file_path,
            remote_path=remote_path or file_path.name,
            file_hash=file_hash,
            file_size=file_size,
            status="success",
            message=upload_result.message,
            metadata=upload_result.metadata,
        )

    def _record_failed_upload(
        self,
        provider_name: str,
        file_path: Path,
        remote_path: str | None,
        file_hash: str,
        file_size: int,
        upload_result: Any,
    ) -> None:
        """Record failed upload in metadata.

        Parameters
        ----------
        provider_name : str
            Provider name.
        file_path : Path
            Local file path.
        remote_path : str, optional
            Remote file path.
        file_hash : str
            File hash.
        file_size : int
            File size.
        upload_result : Any
            Upload result from provider.
        """
        self._metadata_manager.record_backup(
            operation="upload",
            provider=provider_name,
            file_path=file_path,
            remote_path=remote_path or file_path.name,
            file_hash=file_hash,
            file_size=file_size,
            status="failed",
            message=upload_result.message,
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

    def _show_upload_summary(
        self, provider_name: str, success: int, error: int, total: int
    ) -> None:
        """Show upload summary.

        Parameters
        ----------
        provider_name : str
            Provider name.
        success : int
            Number of successful uploads.
        error : int
            Number of failed uploads.
        total : int
            Total number of files.
        """
        from ..config.styles import print_upload_summary

        print_upload_summary(provider_name, success, error, total)
