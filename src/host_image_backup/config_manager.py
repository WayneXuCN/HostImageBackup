"""Configuration management module for Host Image Backup.

This module handles all configuration-related operations including loading,
validating, and saving application and provider configurations.
"""

from pathlib import Path
from typing import Any

import yaml
from loguru import logger

from .config import (
    AppConfig,
    COSConfig,
    GitHubConfig,
    ImgurConfig,
    OSSConfig,
    ProviderConfig,
    SMSConfig,
)


class ConfigManager:
    """Configuration manager for Host Image Backup.

    This class is responsible for loading, validating, and managing
    application and provider configurations.

    Parameters
    ----------
    config_path : Path, optional
        Path to configuration file. If None, uses default location.
    """

    def __init__(self, config_path: Path | None = None):
        """Initialize configuration manager."""
        self._config_path = config_path
        self._config: AppConfig | None = None
        self._provider_classes: dict[str, type[ProviderConfig]] = {
            "oss": OSSConfig,
            "cos": COSConfig,
            "sms": SMSConfig,
            "imgur": ImgurConfig,
            "github": GitHubConfig,
        }

    @property
    def config(self) -> AppConfig:
        """Get current configuration.

        Returns
        -------
        AppConfig
            Current configuration instance.
        """
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def load_config(self, config_path: Path | None = None) -> AppConfig:
        """Load configuration from file.

        Parameters
        ----------
        config_path : Path, optional
            Path to configuration file. If None, uses default location.

        Returns
        -------
        AppConfig
            Loaded configuration instance.

        Raises
        ------
        FileNotFoundError
            If configuration file doesn't exist and no default is available.
        yaml.YAMLError
            If configuration file contains invalid YAML.
        """
        if config_path is None:
            config_path = self._get_config_file()

        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            return AppConfig()

        try:
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse configuration file: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to read configuration file: {e}")
            raise

        # Create base config
        config_data = {
            "default_output_dir": data.get("default_output_dir", "./backup"),
            "max_concurrent_downloads": data.get("max_concurrent_downloads", 5),
            "timeout": data.get("timeout", 30),
            "retry_count": data.get("retry_count", 3),
            "chunk_size": data.get("chunk_size", 8192),
            "log_level": data.get("log_level", "INFO"),
            "providers": {},
        }

        # Load provider configurations
        providers_data = data.get("providers", {})
        for provider_name, provider_class in self._provider_classes.items():
            if provider_name in providers_data:
                provider_data = providers_data[provider_name]
                try:
                    config_data["providers"][provider_name] = provider_class(
                        name=provider_name, **provider_data
                    )
                except Exception as e:
                    logger.warning(f"Failed to load {provider_name} config: {e}")

        self._config = AppConfig(**config_data)
        return self._config

    def save_config(
        self, config: AppConfig | None = None, config_path: Path | None = None
    ) -> None:
        """Save configuration to file.

        Parameters
        ----------
        config : AppConfig, optional
            Configuration to save. If None, saves current configuration.
        config_path : Path, optional
            Path to save configuration file. If None, uses default location.

        Raises
        ------
        PermissionError
            If unable to write to configuration file.
        OSError
            If unable to create configuration directory.
        """
        if config is None:
            config = self.config

        if config_path is None:
            config_path = self._get_config_file()

        try:
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Prepare data for serialization
            data = {
                "default_output_dir": config.default_output_dir,
                "max_concurrent_downloads": config.max_concurrent_downloads,
                "timeout": config.timeout,
                "retry_count": config.retry_count,
                "chunk_size": config.chunk_size,
                "log_level": config.log_level,
                "providers": {},
            }

            # Serialize provider configurations
            for name, provider in config.providers.items():
                data["providers"][name] = provider.dict(exclude={"name"})

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    data, f, default_flow_style=False, allow_unicode=True, indent=2
                )

            logger.info(f"Configuration saved to: {config_path}")

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

    def create_default_config(self) -> None:
        """Create default configuration with all providers.

        This method initializes default configurations for all supported
        providers and saves them to the configuration file.
        """
        try:
            default_providers = {
                "oss": OSSConfig(name="oss"),
                "cos": COSConfig(name="cos"),
                "sms": SMSConfig(name="sms"),
                "imgur": ImgurConfig(name="imgur"),
                "github": GitHubConfig(name="github"),
            }

            self._config = AppConfig(providers=default_providers)
            self.save_config()
            logger.success("Default configuration created successfully")
        except Exception as e:
            logger.error(f"Failed to create default configuration: {e}")
            raise

    def get_provider_config(self, provider_name: str) -> ProviderConfig | None:
        """Get provider configuration.

        Parameters
        ----------
        provider_name : str
            Name of the provider.

        Returns
        -------
        ProviderConfig or None
            Provider configuration if found, None otherwise.
        """
        return self.config.providers.get(provider_name)

    def is_provider_enabled(self, provider_name: str) -> bool:
        """Check if provider is enabled.

        Parameters
        ----------
        provider_name : str
            Name of the provider.

        Returns
        -------
        bool
            True if provider is enabled, False otherwise.
        """
        provider_config = self.get_provider_config(provider_name)
        return provider_config is not None and provider_config.enabled

    def validate_provider_config(self, provider_name: str) -> bool:
        """Validate provider configuration.

        Parameters
        ----------
        provider_name : str
            Name of the provider.

        Returns
        -------
        bool
            True if configuration is valid, False otherwise.
        """
        provider_config = self.get_provider_config(provider_name)
        if provider_config is None:
            return False
        return provider_config.validate_config()

    def update_provider_config(
        self, provider_name: str, config_data: dict[str, Any]
    ) -> None:
        """Update provider configuration.

        Parameters
        ----------
        provider_name : str
            Name of the provider.
        config_data : Dict[str, Any]
            Configuration data to update.

        Raises
        ------
        ValueError
            If provider is not supported.
        """
        if provider_name not in self._provider_classes:
            raise ValueError(f"Unsupported provider: {provider_name}")

        provider_class = self._provider_classes[provider_name]

        # Get existing config or create new one
        existing_config = self.get_provider_config(provider_name)
        if existing_config:
            # Update existing config
            config_dict = existing_config.dict(exclude={"name"})
            config_dict.update(config_data)
            new_config = provider_class(name=provider_name, **config_dict)
        else:
            # Create new config
            new_config = provider_class(name=provider_name, **config_data)

        # Update configuration
        if self._config is None:
            self._config = AppConfig()

        self._config.providers[provider_name] = new_config

    def get_supported_providers(self) -> list[str]:
        """Get list of supported providers.

        Returns
        -------
        list[str]
            List of supported provider names.
        """
        return list(self._provider_classes.keys())

    def _get_config_file(self) -> Path:
        """Get configuration file path.

        Returns
        -------
        Path
            Path to the configuration file.
        """
        if self._config_path:
            return self._config_path

        config_dir = Path.home() / ".config" / "host-image-backup"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.yaml"
