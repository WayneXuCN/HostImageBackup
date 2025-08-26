from pathlib import Path
from typing import Any

from loguru import logger
from rich.console import Console

from ..config.config_manager import ConfigManager
from ..config.config_models import AppConfig
from ..providers.provider_manager import ProviderManager
from ..utils.compression import CompressionService
from ..utils.metadata import MetadataManager
from .backup import BackupExecutor
from .upload import UploadService


class BackupService:
    """Main backup service coordinator for Host Image Backup.

    This class acts as a coordinator, delegating specific tasks to
    specialized service modules while providing a unified API.

    Parameters
    ----------
    config : AppConfig, optional
        Application configuration. If None, loads default configuration.
    config_path : Path, optional
        Path to configuration file.
    """

    def __init__(
        self, config: AppConfig | None = None, config_path: Path | None = None
    ):
        """Initialize backup service coordinator."""
        self._console = Console()
        self._logger = logger

        # Initialize configuration manager
        self._config_manager = ConfigManager(config_path)
        if config:
            self._config_manager._config = config

        # Initialize metadata manager
        self._metadata_manager = MetadataManager()

        # Initialize service modules
        self._provider_manager = ProviderManager(self._config_manager)
        self._backup_executor = BackupExecutor(
            self._provider_manager, self._config_manager, self._metadata_manager
        )
        self._upload_service = UploadService(
            self._provider_manager, self._metadata_manager
        )
        self._compression_service = CompressionService(self._config_manager)

    @property
    def config(self) -> AppConfig:
        """Get current configuration."""
        return self._config_manager.config

    @property
    def metadata_manager(self) -> MetadataManager:
        """Get metadata manager."""
        return self._metadata_manager

    def backup_images(
        self,
        provider_name: str,
        output_dir: Path,
        limit: int | None = None,
        skip_existing: bool = True,
        verbose: bool = False,
    ) -> bool:
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
        bool
            True if backup successful, False otherwise.
        """
        try:
            # Validate requirements
            if not self._backup_executor.validate_backup_requirements(
                provider_name, output_dir
            ):
                return False

            # Execute backup
            result = self._backup_executor.backup_images(
                provider_name=provider_name,
                output_dir=output_dir,
                limit=limit,
                skip_existing=skip_existing,
                verbose=verbose,
            )

            return result.error_count == 0

        except Exception as e:
            self._logger.error(f"Backup operation failed: {e}")
            return False

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
        return self._upload_service.upload_image(
            provider_name=provider_name,
            file_path=file_path,
            remote_path=remote_path,
            verbose=verbose,
        )

    def upload_batch(
        self,
        provider_name: str,
        file_paths: list[Path],
        remote_prefix: str | None = None,
        verbose: bool = False,
    ) -> bool:
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
        bool
            True if all uploads successful, False otherwise.
        """
        try:
            # Validate requirements
            if not self._upload_service.validate_upload_requirements(
                provider_name, file_paths
            ):
                return False

            # Execute batch upload
            result = self._upload_service.upload_batch(
                provider_name=provider_name,
                file_paths=file_paths,
                remote_prefix=remote_prefix,
                verbose=verbose,
            )

            return result.error_count == 0

        except Exception as e:
            self._logger.error(f"Batch upload operation failed: {e}")
            return False

    def compress_images(
        self,
        input_path: Path,
        output_dir: Path,
        quality: int = 85,
        output_format: str | None = None,
        recursive: bool = False,
        skip_existing: bool = True,
        verbose: bool = False,
    ) -> bool:
        """Compress images with high fidelity.

        Parameters
        ----------
        input_path : Path
            File or directory to compress.
        output_dir : Path
            Output directory for compressed files.
        quality : int, default=85
            Compression quality (1-100).
        output_format : str, optional
            Output format (JPEG, PNG, WEBP). If None, uses same as input.
        recursive : bool, default=False
            Recursively compress images in subdirectories.
        skip_existing : bool, default=True
            Skip files that already exist in output directory.
        verbose : bool, default=False
            Enable verbose logging.

        Returns
        -------
        bool
            True if compression successful, False otherwise.
        """
        try:
            # Validate requirements
            if not self._compression_service.validate_compression_requirements(
                input_path, output_dir
            ):
                return False

            # Execute compression
            result = self._compression_service.compress_images(
                input_path=input_path,
                output_dir=output_dir,
                quality=quality,
                output_format=output_format,
                recursive=recursive,
                skip_existing=skip_existing,
                verbose=verbose,
            )

            return result.error_count == 0

        except Exception as e:
            self._logger.error(f"Compression operation failed: {e}")
            return False

    def test_provider(self, provider_name: str) -> bool:
        """Test provider connection.

        Parameters
        ----------
        provider_name : str
            Name of the provider.

        Returns
        -------
        bool
            True if connection test successful, False otherwise.
        """
        return self._provider_manager.test_provider(provider_name)

    def list_providers(self) -> list[str]:
        """List all available providers.

        Returns
        -------
        list[str]
            List of provider names.
        """
        return self._provider_manager.list_providers()

    def get_enabled_providers(self) -> list[str]:
        """Get list of enabled providers.

        Returns
        -------
        list[str]
            List of enabled provider names.
        """
        return self._provider_manager.get_enabled_providers()

    def show_provider_info(self, provider_name: str) -> None:
        """Show provider information.

        Parameters
        ----------
        provider_name : str
            Name of the provider.
        """
        self._provider_manager.show_provider_info(provider_name)

    def get_backup_statistics(self, provider_name: str) -> dict[str, Any]:
        """Get backup statistics for a provider.

        Parameters
        ----------
        provider_name : str
            Name of the provider.

        Returns
        -------
        dict[str, Any]
            Backup statistics.
        """
        return self._backup_executor.get_backup_statistics(provider_name)

    def get_upload_statistics(self, provider_name: str) -> dict[str, Any]:
        """Get upload statistics for a provider.

        Parameters
        ----------
        provider_name : str
            Name of the provider.

        Returns
        -------
        dict[str, Any]
            Upload statistics.
        """
        return self._upload_service.get_upload_statistics(provider_name)

    def estimate_backup_time(
        self, provider_name: str, limit: int | None = None
    ) -> int | None:
        """Estimate backup time in seconds.

        Parameters
        ----------
        provider_name : str
            Name of the provider.
        limit : int, optional
            Maximum number of images to backup.

        Returns
        -------
        int or None
            Estimated time in seconds, or None if cannot estimate.
        """
        return self._backup_executor.estimate_backup_time(provider_name, limit)

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
        return self._upload_service.estimate_upload_time(file_paths)

    def estimate_compression_savings(
        self, input_path: Path, quality: int = 85
    ) -> dict[str, Any] | None:
        """Estimate compression savings.

        Parameters
        ----------
        input_path : Path
            Input file or directory.
        quality : int, default=85
            Compression quality (1-100).

        Returns
        -------
        dict[str, Any] or None
            Estimated compression savings, or None if cannot estimate.
        """
        return self._compression_service.estimate_compression_savings(
            input_path, quality
        )

    def save_config(self, config_path: Path | None = None) -> None:
        """Save current configuration.

        Parameters
        ----------
        config_path : Path, optional
            Path to save configuration file.
        """
        self._config_manager.save_config(config_path=config_path)

    def create_default_config(self) -> None:
        """Create default configuration with all providers."""
        self._config_manager.create_default_config()

    def update_provider_config(
        self, provider_name: str, config_data: dict[str, Any]
    ) -> None:
        """Update provider configuration.

        Parameters
        ----------
        provider_name : str
            Name of the provider.
        config_data : dict[str, Any]
            Configuration data to update.
        """
        self._config_manager.update_provider_config(provider_name, config_data)
        # Clear provider cache to use new configuration
        self._provider_manager.clear_cache()

    def get_system_status(self) -> dict[str, Any]:
        """Get overall system status.

        Returns
        -------
        dict[str, Any]
            System status information.
        """
        try:
            # Get configuration status
            enabled_providers = self.get_enabled_providers()
            supported_providers = self.list_providers()

            # Test all enabled providers
            provider_status = {}
            for provider_name in enabled_providers:
                provider_status[provider_name] = {
                    "connection": self.test_provider(provider_name),
                    "config_valid": self._provider_manager.validate_provider_config(
                        provider_name
                    ),
                    "statistics": self.get_backup_statistics(provider_name),
                }

            # Get overall statistics
            all_stats = self._metadata_manager.get_statistics()

            return {
                "enabled_providers": enabled_providers,
                "supported_providers": supported_providers,
                "provider_count": len(enabled_providers),
                "provider_status": provider_status,
                "overall_statistics": all_stats,
                "config_path": str(self._config_manager._get_config_file()),
            }
        except Exception as e:
            self._logger.error(f"Failed to get system status: {e}")
            return {"error": str(e)}

    def refresh_providers(self) -> None:
        """Refresh all provider instances."""
        self._provider_manager.clear_cache()

    def get_provider_info(self, provider_name: str) -> dict[str, Any]:
        """Get detailed provider information.

        Parameters
        ----------
        provider_name : str
            Name of the provider.

        Returns
        -------
        dict[str, Any]
            Provider information.
        """
        return self._provider_manager.get_provider_info(provider_name)
