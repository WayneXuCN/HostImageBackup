from typing import Any

from loguru import logger
from rich.console import Console

from .base import BaseProvider
from .cos import COSProvider
from .github import GitHubProvider
from .imgur import ImgurProvider
from .oss import OSSProvider
from .sms import SMSProvider

try:
    from importlib.metadata import EntryPoint, entry_points
except Exception:
    entry_points = None
    EntryPoint = object


class ProviderManager:
    """Provider manager for Host Image Backup.

    This class is responsible for managing provider instances,
    including creation, validation, and lifecycle management.

    Parameters
    ----------
    config_manager : ConfigManager
        Configuration manager instance.
    """

    def __init__(self, config_manager: Any):
        """Initialize provider manager."""
        self._config_manager = config_manager
        self._console = Console()
        self._logger = logger

        # Provider class mapping (initially includes built-in)
        self._provider_classes: dict[str, type[BaseProvider]] = {
            "oss": OSSProvider,
            "cos": COSProvider,
            "sms": SMSProvider,
            "imgur": ImgurProvider,
            "github": GitHubProvider,
        }

        # Flag: whether dynamic discovery has been performed
        self._discovered = False

        # Cache for provider instances
        self._provider_cache: dict[str, BaseProvider] = {}

    def get_provider(self, provider_name: str) -> BaseProvider | None:
        """Get provider instance.

        Parameters
        ----------
        provider_name : str
            Name of the provider.

        Returns
        -------
        BaseProvider or None
            Provider instance if successful, None otherwise.
        """
        # Ensure dynamic discovery has been performed
        self._ensure_discovery()

        # Check cache first
        if provider_name in self._provider_cache:
            return self._provider_cache[provider_name]

        # Get provider configuration
        provider_config = self._config_manager.get_provider_config(provider_name)
        if not provider_config:
            self._logger.error(f"Provider configuration not found: {provider_name}")
            return None

        # Check if provider is enabled
        if not provider_config.enabled:
            self._logger.error(f"Provider not enabled: {provider_name}")
            return None

        # Validate configuration
        if not provider_config.validate_config():
            self._logger.error(f"Invalid provider configuration: {provider_name}")
            return None

        # Get provider class
        provider_class = self._provider_classes.get(provider_name)
        if not provider_class:
            self._logger.error(f"Provider implementation not found: {provider_name}")
            return None

        # Create provider instance
        try:
            provider = provider_class(provider_config)
            self._provider_cache[provider_name] = provider
            return provider
        except Exception as e:
            self._logger.error(f"Failed to create provider {provider_name}: {e}")
            return None

    def test_provider(self, provider_name: str) -> bool:
        """Test provider connection.

        Parameters
        ----------
        provider_name : str
            Name of the provider.

        Returns
        -------
        bool
            True if connection test is successful, False otherwise.
        """
        provider = self.get_provider(provider_name)
        if not provider:
            return False

        try:
            result = provider.test_connection()
            if result:
                self._console.print(
                    f"[green]Provider {provider_name} connection test successful[/green]"
                )
            else:
                self._console.print(
                    f"[red]Provider {provider_name} connection test failed[/red]"
                )
            return result
        except Exception as e:
            self._console.print(
                f"[red]Provider {provider_name} connection test exception: {e}[/red]"
            )
            return False

    def get_provider_info(self, provider_name: str) -> dict[str, Any]:
        """Get provider information.

        Parameters
        ----------
        provider_name : str
            Name of the provider.

        Returns
        -------
        Dict[str, Any]
            Provider information dictionary.
        """
        provider = self.get_provider(provider_name)
        if not provider:
            return {}

        # Test connection
        connection_status = "Normal" if provider.test_connection() else "Failed"

        # Get image count
        try:
            image_count = provider.get_image_count()
            count_text = (
                str(image_count) if image_count is not None else "Not available"
            )
        except Exception as e:
            self._logger.error(f"Error getting image count for {provider_name}: {e}")
            count_text = "Failed to get"

        return {
            "name": provider_name.upper(),
            "status": "Enabled" if provider.is_enabled() else "Disabled",
            "connection_status": connection_status,
            "image_count": count_text,
            "config_valid": "Yes" if provider.validate_config() else "No",
        }

    def show_provider_info(self, provider_name: str) -> None:
        """Show provider information in a formatted way.

        Parameters
        ----------
        provider_name : str
            Name of the provider.
        """
        info = self.get_provider_info(provider_name)
        if not info:
            from ..config.styles import print_error

            print_error(f"Cannot get provider: {provider_name}")
            return

        from ..config.styles import console, print_header

        print_header(f"{provider_name.upper()} Provider Information")
        console.print()

        console.print(f"[cyan]Name:[/cyan] {info['name']}")
        status_color = "green" if info["status"] == "Enabled" else "red"
        console.print(
            f"[cyan]Status:[/cyan] [{status_color}]{info['status']}[/{status_color}]"
        )
        connection_color = "green" if info["connection_status"] == "Normal" else "red"
        console.print(
            f"[cyan]Connection Test:[/cyan] [{connection_color}]{info['connection_status']}[/{connection_color}]"
        )
        console.print(f"[cyan]Image Count:[/cyan] {info['image_count']}")
        config_color = "green" if info["config_valid"] == "Yes" else "red"
        console.print(
            f"[cyan]Configuration Valid:[/cyan] [{config_color}]{info['config_valid']}[/{config_color}]"
        )
        console.print()

    def list_providers(self) -> list[str]:
        """List all available providers.

        Returns
        -------
        list[str]
            List of provider names.
        """
        self._ensure_discovery()
        return list(self._provider_classes.keys())

    def get_enabled_providers(self) -> list[str]:
        """Get list of enabled providers.

        Returns
        -------
        list[str]
            List of enabled provider names.
        """
        enabled_providers = []
        for provider_name in self.list_providers():
            if self._config_manager.is_provider_enabled(provider_name):
                enabled_providers.append(provider_name)
        return enabled_providers

    def validate_all_providers(self) -> dict[str, bool]:
        """Validate all configured providers.

        Returns
        -------
        Dict[str, bool]
            Dictionary mapping provider names to validation results.
        """
        results = {}
        for provider_name in self.list_providers():
            if self._config_manager.is_provider_enabled(provider_name):
                results[provider_name] = self.validate_provider_config(provider_name)
        return results

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
        return self._config_manager.validate_provider_config(provider_name)

    def clear_cache(self) -> None:
        """Clear provider instance cache."""
        self._provider_cache.clear()

    def refresh_provider(self, provider_name: str) -> BaseProvider | None:
        """Refresh provider instance.

        Parameters
        ----------
        provider_name : str
            Name of the provider.

        Returns
        -------
        BaseProvider or None
            New provider instance if successful, None otherwise.
        """
        # Remove from cache
        if provider_name in self._provider_cache:
            del self._provider_cache[provider_name]

        # Get fresh instance
        return self.get_provider(provider_name)

    def get_provider_class(self, provider_name: str) -> type[BaseProvider] | None:
        """Get provider class.

        Parameters
        ----------
        provider_name : str
            Name of the provider.

        Returns
        -------
        Type[BaseProvider] or None
            Provider class if found, None otherwise.
        """
        self._ensure_discovery()
        return self._provider_classes.get(provider_name)

    def register_provider(
        self, provider_name: str, provider_class: type[BaseProvider]
    ) -> None:
        """Register a new provider class.

        Parameters
        ----------
        provider_name : str
            Name of the provider.
        provider_class : Type[BaseProvider]
            Provider class to register.
        """
        self._provider_classes[provider_name] = provider_class
        self._logger.info(f"Registered provider: {provider_name}")

    # ---------- Internal implementation of dynamic discovery ----------
    def _ensure_discovery(self) -> None:
        """Lazy discover providers via entry points once.

        Idempotent: only executed on first call. Subsequent calls return immediately.
        """
        if self._discovered:
            return
        self._discovered = True

        if entry_points is None:  # pragma: no cover
            self._logger.warning(
                "importlib.metadata.entry_points not available, skipping dynamic discovery."
            )
            return
        try:
            eps = entry_points()
            group_name = "host_image_backup.providers"
            if hasattr(eps, "select"):
                selected = eps.select(group=group_name)
            elif isinstance(eps, dict):
                selected = eps.get(group_name, [])
            else:
                selected = (
                    getattr(eps, group_name, []) if hasattr(eps, group_name) else []
                )

            added = []
            for ep in selected:
                name = getattr(ep, "name", None)
                if not name or name in self._provider_classes:
                    if name in self._provider_classes:
                        self._logger.debug(
                            f"Entry point provider '{name}' already exists (built-in or registered), ignored."
                        )
                    continue
                try:
                    obj = ep.load()
                    if not isinstance(obj, type) or not issubclass(obj, BaseProvider):
                        self._logger.error(
                            f"Entry point '{name}' object is not a subclass of BaseProvider, ignored."
                        )
                        continue
                    self._provider_classes[name] = obj
                    added.append(name)
                except Exception as exc:  # pragma: no cover - just log
                    self._logger.error(
                        f"Failed to load provider entry point '{name}': {exc}"
                    )
            if added:
                self._logger.info(
                    "Dynamically discovered provider(s): " + ", ".join(sorted(added))
                )
            else:
                self._logger.debug("No new providers discovered dynamically.")
        except Exception as e:  # pragma: no cover
            self._logger.error(f"Failed to scan provider entry points: {e}")

    def is_provider_supported(self, provider_name: str) -> bool:
        """Check if provider is supported.

        Parameters
        ----------
        provider_name : str
            Name of the provider.

        Returns
        -------
        bool
            True if provider is supported, False otherwise.
        """
        return provider_name in self._provider_classes
