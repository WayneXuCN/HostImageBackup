import concurrent.futures
from pathlib import Path

from loguru import logger
from rich.console import Console
from rich.panel import Panel

from .config import AppConfig
from .metadata import MetadataManager
from .providers import BaseProvider, ImageInfo
from .providers.base import SUPPORTED_IMAGE_EXTENSIONS
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

        # Initialize metadata manager
        self.metadata_manager = MetadataManager()

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

            # Create a custom progress bar with our consistent styling
            from .styles import create_backup_progress_bar
            with create_backup_progress_bar() as progress:
                # If we don't know the total, use an indefinite progress bar
                backup_task = progress.add_task(
                    f"Backing up {provider_name}",
                    total=total_count if total_count else None,
                )

                # Create thread pool executor
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=self.config.max_concurrent_downloads
                ) as executor:
                    # Store image info and output file mapping
                    download_tasks = []

                    for image_info in provider.list_images(limit=limit):
                        # Build output file path
                        output_file = provider_dir / self._sanitize_filename(
                            image_info.filename
                        )

                        # Skip if file exists and skip_existing is True
                        if skip_existing and output_file.exists():
                            skip_count += 1
                            # Record skipped operation in metadata
                            self.metadata_manager.record_backup(
                                operation="download",
                                provider=provider_name,
                                file_path=output_file,
                                remote_path=image_info.url or image_info.filename,
                                file_hash="",  # No hash for skipped files
                                file_size=0,   # No size for skipped files
                                status="skipped",
                                message="File already exists and skip_existing is True",
                            )
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
                        download_tasks.append((future, image_info, output_file))

                    # Wait for all downloads to complete
                    for future, image_info, output_file in download_tasks:
                        try:
                            result = future.result()
                            if result:
                                success_count += 1
                                # Record successful download in metadata
                                file_hash = self.metadata_manager.get_file_hash(output_file) if output_file.exists() else ""
                                file_size = output_file.stat().st_size if output_file.exists() else 0
                                self.metadata_manager.record_backup(
                                    operation="download",
                                    provider=provider_name,
                                    file_path=output_file,
                                    remote_path=image_info.url or image_info.filename,
                                    file_hash=file_hash,
                                    file_size=file_size,
                                    status="success",
                                    message="Download completed successfully",
                                )

                                # Update image metadata for statistics
                                if output_file.exists():
                                    try:
                                        # Try to get image dimensions (optional)
                                        width = None
                                        height = None
                                        format = None
                                        try:
                                            from PIL import Image
                                            with Image.open(output_file) as img:
                                                width, height = img.size
                                                format = img.format
                                        except Exception:
                                            pass  # Ignore if PIL is not available or fails

                                        self.metadata_manager.update_file_metadata(
                                            file_path=output_file,
                                            file_hash=file_hash,
                                            file_size=file_size,
                                            width=width,
                                            height=height,
                                            format=format,
                                        )
                                    except Exception as e:
                                        self.logger.warning(f"Failed to update image metadata for {output_file}: {e}")
                            else:
                                error_count += 1
                                # Record failed download in metadata
                                self.metadata_manager.record_backup(
                                    operation="download",
                                    provider=provider_name,
                                    file_path=output_file,
                                    remote_path=image_info.url or image_info.filename,
                                    file_hash="",
                                    file_size=0,
                                    status="failed",
                                    message="Download failed",
                                )
                        except Exception as e:
                            error_count += 1
                            # Record failed download in metadata
                            self.metadata_manager.record_backup(
                                operation="download",
                                provider=provider_name,
                                file_path=output_file,
                                remote_path=image_info.url or image_info.filename,
                                file_hash="",
                                file_size=0,
                                status="failed",
                                message=f"Download exception: {str(e)}",
                            )
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
        from .styles import print_backup_summary
        print_backup_summary(provider_name, success, error, skip)

    def show_provider_info(self, provider_name: str) -> None:
        """Show provider information"""
        provider = self.get_provider(provider_name)
        if not provider:
            from .styles import print_error
            print_error(f"Cannot get provider: {provider_name}")
            return

        # Test connection
        connection_status = (
            "Normal"
            if provider.test_connection()
            else "Failed"
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

        from .styles import print_header, console
        print_header(f"{provider_name.upper()} Provider Information")
        console.print()
        
        console.print(f"[cyan]Name:[/cyan] {provider_name.upper()}")
        status_text = "Enabled" if provider.is_enabled() else "Disabled"
        status_color = "green" if provider.is_enabled() else "red"
        console.print(f"[cyan]Status:[/cyan] [{status_color}]{status_text}[/{status_color}]")
        connection_color = "green" if connection_status == "Normal" else "red"
        console.print(f"[cyan]Connection Test:[/cyan] [{connection_color}]{connection_status}[/{connection_color}]")
        console.print(f"[cyan]Image Count:[/cyan] {count_text}")
        config_valid = "Yes" if provider.validate_config() else "No"
        config_color = "green" if provider.validate_config() else "red"
        console.print(f"[cyan]Configuration Valid:[/cyan] [{config_color}]{config_valid}[/{config_color}]")
        console.print()

    def upload_image(
        self,
        provider_name: str,
        file_path: Path,
        remote_path: str | None = None,
        verbose: bool = False,
    ) -> bool:
        """Upload image to provider

        Parameters
        ----------
        provider_name : str
            Provider name.
        file_path : Path
            Local file path to upload.
        remote_path : str, optional
            Remote path for the file.
        verbose : bool, default=False
            Show detailed logs.

        Returns
        -------
        bool
            True if upload was successful, False otherwise.
        """
        provider = self.get_provider(provider_name)
        if not provider:
            return False

        try:
            # Check if file exists
            if not file_path.exists():
                self.console.print(f"[red]File not found: {file_path}[/red]")
                return False

            # Calculate file hash
            file_hash = self.metadata_manager.get_file_hash(file_path)
            file_size = file_path.stat().st_size

            self.console.print(
                Panel(
                    f"[cyan]Uploading {file_path.name} to {provider_name}[/cyan]\n"
                    f"[blue]File size: {file_size:,} bytes[/blue]",
                    title="Upload Started",
                    border_style="blue",
                )
            )

            # Upload image
            result = provider.upload_image(file_path, remote_path)

            # Record operation in metadata
            if result.success:
                self.metadata_manager.record_backup(
                    operation="upload",
                    provider=provider_name,
                    file_path=file_path,
                    remote_path=remote_path or file_path.name,
                    file_hash=file_hash,
                    file_size=file_size,
                    status="success",
                    message=result.message,
                    metadata=result.metadata,
                )

                # Show success message
                self.console.print()
                self.console.print("[green]✓ Upload successful![/green]")
                if result.url:
                    self.console.print(f"[blue]URL: {result.url}[/blue]")

                return True
            else:
                # Record failed operation
                self.metadata_manager.record_backup(
                    operation="upload",
                    provider=provider_name,
                    file_path=file_path,
                    remote_path=remote_path or file_path.name,
                    file_hash=file_hash,
                    file_size=file_size,
                    status="failed",
                    message=result.message,
                )

                self.console.print()
                self.console.print(f"[red]✗ Upload failed: {result.message}[/red]")
                return False

        except Exception as e:
            self.logger.error(f"Upload process error: {e}")
            self.console.print(f"[red]Upload error: {str(e)}[/red]")
            return False

    def upload_batch(
        self,
        provider_name: str,
        file_paths: list[Path],
        remote_prefix: str | None = None,
        verbose: bool = False,
    ) -> bool:
        """Upload multiple images to provider

        Parameters
        ----------
        provider_name : str
            Provider name.
        file_paths : list[Path]
            List of local file paths to upload.
        remote_prefix : str, optional
            Remote prefix for all files.
        verbose : bool, default=False
            Show detailed logs.

        Returns
        -------
        bool
            True if all uploads were successful, False otherwise.
        """
        provider = self.get_provider(provider_name)
        if not provider:
            return False

        total_files = len(file_paths)
        success_count = 0
        error_count = 0

        self.console.print(
            Panel(
                f"[cyan]Starting batch upload to {provider_name}[/cyan]\n"
                f"[blue]Total files: {total_files}[/blue]",
                title="Batch Upload",
                border_style="blue",
            )
        )

        # Create progress bar
        from .styles import create_backup_progress_bar
        with create_backup_progress_bar() as progress:
            upload_task = progress.add_task(
                f"Uploading to {provider_name}",
                total=total_files,
            )

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
                    self.logger.error(f"Batch upload error for {file_path}: {e}")

                progress.update(upload_task, advance=1)

        # Show summary
        self.console.print()
        self._show_upload_summary(
            provider_name, success_count, error_count, total_files
        )

        return error_count == 0

    def _show_upload_summary(
        self, provider_name: str, success: int, error: int, total: int
    ) -> None:
        """Show upload summary"""
        from .styles import print_upload_summary
        print_upload_summary(provider_name, success, error, total)

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
        """Compress images with high fidelity

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
            Show detailed logs.

        Returns
        -------
        bool
            True if compression was successful, False otherwise.
        """
        try:
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)

            # Collect files to compress
            files_to_compress = []

            if input_path.is_file():
                if input_path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                    files_to_compress.append(input_path)
                else:
                    self.console.print(f"[red]Unsupported file format: {input_path}[/red]")
                    return False
            else:
                # Directory processing
                pattern = "**/*" if recursive else "*"
                for file_path in input_path.glob(pattern):
                    if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                        files_to_compress.append(file_path)

            if not files_to_compress:
                self.console.print("[yellow]No image files found to compress[/yellow]")
                return False

            success_count = 0
            error_count = 0
            skip_count = 0

            # Create progress bar
            from .styles import create_backup_progress_bar
            with create_backup_progress_bar() as progress:
                compress_task = progress.add_task(
                    "Compressing images",
                    total=len(files_to_compress),
                )

                # Process each file
                for file_path in files_to_compress:
                    try:
                        # Determine output file path
                        relative_path = file_path.relative_to(input_path) if input_path.is_dir() else Path(file_path.name)

                        # Determine output format
                        if output_format:
                            output_ext = f".{output_format.lower()}"
                        else:
                            output_ext = file_path.suffix.lower()

                        # For JPEG, use .jpg extension
                        if output_ext == ".jpeg":
                            output_ext = ".jpg"

                        output_file = output_dir / relative_path.with_suffix(output_ext)

                        # Create output subdirectory if needed
                        output_file.parent.mkdir(parents=True, exist_ok=True)

                        # Skip if file exists and skip_existing is True
                        if skip_existing and output_file.exists():
                            skip_count += 1
                            if verbose:
                                self.console.print(f"[yellow]Skipping existing file: {output_file}[/yellow]")
                            progress.update(compress_task, advance=1)
                            continue

                        # Compress image
                        if self._compress_single_image(file_path, output_file, quality, output_format):
                            success_count += 1
                            if verbose:
                                self.console.print(f"[green]Compressed: {file_path.name} -> {output_file.name}[/green]")
                        else:
                            error_count += 1
                            if verbose:
                                self.console.print(f"[red]Failed to compress: {file_path.name}[/red]")

                    except Exception as e:
                        error_count += 1
                        self.logger.error(f"Compression error for {file_path}: {e}")
                        if verbose:
                            self.console.print(f"[red]Error compressing {file_path.name}: {e}[/red]")

                    progress.update(compress_task, advance=1)

            # Show summary
            self.console.print()
            self._show_compression_summary(success_count, error_count, skip_count, len(files_to_compress))

            return error_count == 0

        except Exception as e:
            self.logger.error(f"Compression process error: {e}")
            self.console.print(f"[red]Compression error: {str(e)}[/red]")
            return False

    def _compress_single_image(
        self,
        input_file: Path,
        output_file: Path,
        quality: int,
        output_format: str | None = None
    ) -> bool:
        """Compress a single image file

        Parameters
        ----------
        input_file : Path
            Input image file path.
        output_file : Path
            Output image file path.
        quality : int
            Compression quality (1-100).
        output_format : str, optional
            Output format (JPEG, PNG, WEBP).

        Returns
        -------
        bool
            True if compression was successful, False otherwise.
        """
        try:
            from PIL import Image

            # Open image
            with Image.open(input_file) as img:
                # Convert RGBA to RGB for JPEG format
                if ((output_format and output_format.upper() == "JPEG") or \
                   (not output_format and input_file.suffix.lower() in [".png", ".webp"])) and \
                   img.mode in ("RGBA", "LA", "P"):
                    # Create white background for transparency
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    img = background

                # Determine format
                if output_format:
                    format = output_format.upper()
                else:
                    format = img.format if img.format else "JPEG"

                # Save with compression
                save_kwargs = {}
                if format in ["JPEG", "WEBP"]:
                    save_kwargs["quality"] = quality
                    save_kwargs["optimize"] = True

                if format == "PNG":
                    # For PNG, quality parameter is not used, but we can optimize
                    save_kwargs["optimize"] = True

                img.save(output_file, format=format, **save_kwargs)

            return True

        except Exception as e:
            self.logger.error(f"Failed to compress {input_file}: {e}")
            return False

    def _show_compression_summary(
        self, success: int, error: int, skip: int, total: int
    ) -> None:
        """Show compression summary"""
        from .styles import print_compression_summary
        print_compression_summary(success, error, skip, total)
