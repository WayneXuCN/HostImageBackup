from pathlib import Path

import yaml
from loguru import logger
from pydantic import BaseModel, Field, field_validator

try:
    from importlib.metadata import EntryPoint, entry_points
except Exception:
    entry_points = None
    EntryPoint = object


class ProviderConfig(BaseModel):
    """Base configuration class for image hosting providers.

    Parameters
    ----------
    name : str
        The name of the provider.
    enabled : bool, default=True
        Whether the provider is enabled.
    prefix : str, default=""
        The prefix path for images in the provider.

    Examples
    --------
    >>> config = ProviderConfig(name="example")
    >>> config.enabled
    True
    """

    name: str
    enabled: bool = Field(default=True, description="Whether the provider is enabled")
    prefix: str = Field(default="", description="Prefix path for images")

    def validate_config(self) -> bool:
        """Validate the provider configuration.

        Returns
        -------
        bool
            True if configuration is valid, False otherwise.
        """
        return True

    # --- Registry hooks ---
    @classmethod
    def register(cls, name: str) -> None:
        """Register config class manually.

        Typically used by internal providers; external plugins rely on entry points.
        """
        ConfigRegistry.register(name, cls)


class ConfigRegistry:
    """Central registry for ProviderConfig classes.

    双通道：
    1. 代码内显式 ProviderConfig.register(name)
    2. entry points: group `host_image_backup.provider_configs`
    """

    _providers: dict[str, type[ProviderConfig]] = {}
    _discovered: bool = False

    @classmethod
    def register(cls, name: str, config_class: type[ProviderConfig]) -> None:
        if name in cls._providers:
            logger.debug(
                f"ConfigRegistry: provider config '{name}' already registered, skip"
            )
            return
        cls._providers[name] = config_class

    @classmethod
    def discover_entry_points(cls) -> None:
        if cls._discovered:
            return
        cls._discovered = True
        if entry_points is None:
            logger.debug("ConfigRegistry: entry_points not available, skip discovery")
            return
        try:
            eps = entry_points()
            group = "host_image_backup.provider_configs"
            if hasattr(eps, "select"):
                selected = eps.select(group=group)
            else:
                selected = eps[group] if isinstance(eps, dict) else []
            if not isinstance(selected, list | tuple | set):
                selected = [selected] if selected else []
            added = []
            for ep in selected:
                name = getattr(ep, "name", None)
                if not name or name in cls._providers:
                    continue
                try:
                    obj = ep.load()
                    if not isinstance(obj, type) or not issubclass(obj, ProviderConfig):
                        logger.error(
                            f"ConfigRegistry: entry point '{name}' not a ProviderConfig subclass"
                        )
                        continue
                    cls._providers[name] = obj
                    added.append(name)
                except Exception as exc:
                    logger.error(f"ConfigRegistry: failed loading '{name}': {exc}")
            if added:
                logger.info(
                    "ConfigRegistry: discovered provider configs: "
                    + ", ".join(sorted(added))
                )
        except Exception as e:
            logger.error(f"ConfigRegistry: discovery failed: {e}")

    @classmethod
    def get(cls, name: str) -> type[ProviderConfig] | None:
        return cls._providers.get(name)

    @classmethod
    def all(cls) -> dict[str, type[ProviderConfig]]:
        cls.discover_entry_points()
        return dict(cls._providers)


class OSSConfig(ProviderConfig):
    """Alibaba Cloud OSS configuration.

    Parameters
    ----------
    access_key_id : str, default=""
        The access key ID for OSS.
    access_key_secret : str, default=""
        The access key secret for OSS.
    bucket : str, default=""
        The bucket name.
    endpoint : str, default=""
        The OSS endpoint URL.

    Examples
    --------
    >>> config = OSSConfig(
    ...     name="oss",
    ...     access_key_id="key_id",
    ...     access_key_secret="secret",
    ...     bucket="my-bucket",
    ...     endpoint="oss-cn-hangzhou.aliyuncs.com"
    ... )
    >>> config.validate_config()
    True
    """

    access_key_id: str = Field(default="", description="OSS access key ID")
    access_key_secret: str = Field(default="", description="OSS access key secret")
    bucket: str = Field(default="", description="OSS bucket name")
    endpoint: str = Field(default="", description="OSS endpoint")

    def validate_config(self) -> bool:
        """Validate OSS configuration.

        Returns
        -------
        bool
            True if all required fields are provided, False otherwise.
        """
        required_fields = [
            self.access_key_id,
            self.access_key_secret,
            self.bucket,
            self.endpoint,
        ]
        return all(field.strip() for field in required_fields)


class COSConfig(ProviderConfig):
    """Tencent Cloud COS configuration.

    Parameters
    ----------
    secret_id : str, default=""
        The secret ID for COS.
    secret_key : str, default=""
        The secret key for COS.
    bucket : str, default=""
        The bucket name.
    region : str, default=""
        The COS region.

    Examples
    --------
    >>> config = COSConfig(
    ...     name="cos",
    ...     secret_id="secret_id",
    ...     secret_key="secret_key",
    ...     bucket="my-bucket",
    ...     region="ap-guangzhou"
    ... )
    >>> config.validate_config()
    True
    """

    secret_id: str = Field(default="", description="COS secret ID")
    secret_key: str = Field(default="", description="COS secret key")
    bucket: str = Field(default="", description="COS bucket name")
    region: str = Field(default="", description="COS region")

    def validate_config(self) -> bool:
        """Validate COS configuration.

        Returns
        -------
        bool
            True if all required fields are provided, False otherwise.
        """
        required_fields = [self.secret_id, self.secret_key, self.bucket, self.region]
        return all(field.strip() for field in required_fields)


class SMSConfig(ProviderConfig):
    """SM.MS configuration.

    Parameters
    ----------
    api_token : str, default=""
        The API token for SM.MS.

    Examples
    --------
    >>> config = SMSConfig(name="sms", api_token="your_token")
    >>> config.validate_config()
    True
    """

    api_token: str = Field(default="", description="SM.MS API token")

    def validate_config(self) -> bool:
        """Validate SM.MS configuration.

        Returns
        -------
        bool
            True if API token is provided, False otherwise.
        """
        return bool(self.api_token.strip())


class ImgurConfig(ProviderConfig):
    """Imgur configuration.

    Parameters
    ----------
    client_id : str, default=""
        The client ID for Imgur API.
    client_secret : str, default=""
        The client secret for Imgur API.
    access_token : str, default=""
        The access token for Imgur API.
    refresh_token : str, default=""
        The refresh token for Imgur API.

    Examples
    --------
    >>> config = ImgurConfig(
    ...     name="imgur",
    ...     client_id="client_id",
    ...     client_secret="client_secret",
    ...     access_token="access_token"
    ... )
    >>> config.validate_config()
    True
    """

    client_id: str = Field(default="", description="Imgur client ID")
    client_secret: str = Field(default="", description="Imgur client secret")
    access_token: str = Field(default="", description="Imgur access token")
    refresh_token: str = Field(default="", description="Imgur refresh token")

    def validate_config(self) -> bool:
        """Validate Imgur configuration.

        Returns
        -------
        bool
            True if required fields are provided, False otherwise.
        """
        required_fields = [self.client_id, self.client_secret, self.access_token]
        return all(field.strip() for field in required_fields)


class GitHubConfig(ProviderConfig):
    """GitHub configuration.

    Parameters
    ----------
    token : str, default=""
        The GitHub personal access token.
    owner : str, default=""
        The repository owner username.
    repo : str, default=""
        The repository name.
    path : str, default=""
        The path within the repository where images are stored.

    Examples
    --------
    >>> config = GitHubConfig(
    ...     name="github",
    ...     token="ghp_token",
    ...     owner="username",
    ...     repo="repo-name"
    ... )
    >>> config.validate_config()
    True
    """

    token: str = Field(default="", description="GitHub personal access token")
    owner: str = Field(default="", description="Repository owner")
    repo: str = Field(default="", description="Repository name")
    path: str = Field(default="", description="Path within repository")

    def validate_config(self) -> bool:
        """Validate GitHub configuration.

        Returns
        -------
        bool
            True if required fields are provided, False otherwise.
        """
        required_fields = [self.token, self.owner, self.repo]
        return all(field.strip() for field in required_fields)


class AppConfig(BaseModel):
    """Application configuration.

    Parameters
    ----------
    default_output_dir : str, default="./backup"
        Default directory for backup output.
    max_concurrent_downloads : int, default=5
        Maximum number of concurrent downloads.
    timeout : int, default=30
        Request timeout in seconds.
    retry_count : int, default=3
        Number of retry attempts for failed downloads.
    chunk_size : int, default=8192
        Download chunk size in bytes.
    log_level : str, default="INFO"
        Logging level.
    providers : Dict[str, ProviderConfig], default={}
        Dictionary of provider configurations.

    Examples
    --------
    >>> config = AppConfig()
    >>> config.default_output_dir
    './backup'
    >>> config.max_concurrent_downloads
    5
    """

    default_output_dir: str = Field(
        default="./backup", description="Default output directory for backups"
    )
    max_concurrent_downloads: int = Field(
        default=5, ge=1, le=20, description="Maximum concurrent downloads"
    )
    timeout: int = Field(
        default=30, ge=5, le=300, description="Request timeout in seconds"
    )
    retry_count: int = Field(
        default=3, ge=0, le=10, description="Number of retry attempts"
    )
    chunk_size: int = Field(
        default=8192, ge=1024, description="Download chunk size in bytes"
    )
    log_level: str = Field(default="INFO", description="Logging level")
    providers: dict = Field(default_factory=dict, description="Provider configurations")

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level value.

        Parameters
        ----------
        v : str
            The log level value to validate.

        Returns
        -------
        str
            The validated log level.

        Raises
        ------
        ValueError
            If log level is invalid.
        """
        valid_levels = [
            "TRACE",
            "DEBUG",
            "INFO",
            "SUCCESS",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ]
        if isinstance(v, str) and v.upper() in valid_levels:
            return v.upper()
        raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")

    @classmethod
    def get_config_dir(cls) -> Path:
        """Get configuration directory path.

        Returns
        -------
        Path
            Path to the configuration directory.
        """
        config_dir = Path.home() / ".config" / "host-image-backup"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    @classmethod
    def get_config_file(cls) -> Path:
        """Get configuration file path.

        Returns
        -------
        Path
            Path to the configuration file.
        """
        return cls.get_config_dir() / "config.yaml"

    @classmethod
    def load(cls, config_path: Path | None = None) -> "AppConfig":
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
            config_path = cls.get_config_file()

        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            return cls()

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

        # Load provider configurations (dynamic)
        providers_data = data.get("providers", {})
        # Ensure built-in configs registered
        OSSConfig.register("oss")
        COSConfig.register("cos")
        SMSConfig.register("sms")
        ImgurConfig.register("imgur")
        GitHubConfig.register("github")
        # Discover external
        ConfigRegistry.discover_entry_points()
        for provider_name, provider_class in ConfigRegistry.all().items():
            if provider_name in providers_data:
                provider_data = providers_data[provider_name] or {}
                try:
                    config_data["providers"][provider_name] = provider_class(
                        name=provider_name, **provider_data
                    )
                except Exception as e:
                    logger.warning(f"Failed to load {provider_name} config: {e}")

        return cls(**config_data)

    def save(self, config_path: Path | None = None) -> None:
        """Save configuration to file.

        Parameters
        ----------
        config_path : Path, optional
            Path to save configuration file. If None, uses default location.

        Raises
        ------
        PermissionError
            If unable to write to configuration file.
        OSError
            If unable to create configuration directory.
        """
        if config_path is None:
            config_path = self.get_config_file()

        try:
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Prepare data for serialization
            data = {
                "default_output_dir": self.default_output_dir,
                "max_concurrent_downloads": self.max_concurrent_downloads,
                "timeout": self.timeout,
                "retry_count": self.retry_count,
                "chunk_size": self.chunk_size,
                "log_level": self.log_level,
                "providers": {},
            }

            # Serialize provider configurations
            for name, provider in self.providers.items():
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
            # Register built-in & discover third-party
            OSSConfig.register("oss")
            COSConfig.register("cos")
            SMSConfig.register("sms")
            ImgurConfig.register("imgur")
            GitHubConfig.register("github")
            ConfigRegistry.discover_entry_points()
            self.providers = {
                name: cls(name=name) for name, cls in ConfigRegistry.all().items()
            }
            self.save()
            logger.success("Default configuration created successfully")
        except Exception as e:
            logger.error(f"Failed to create default configuration: {e}")
            raise
