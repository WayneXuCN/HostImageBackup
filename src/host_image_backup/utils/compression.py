from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger
from rich.console import Console

from ..providers.base import SUPPORTED_IMAGE_EXTENSIONS
from .file_utils import FileUtils


@dataclass
class CompressionResult:
    """Compression operation result.

    Parameters
    ----------
    success_count : int
        Number of successful compressions.
    error_count : int
        Number of failed compressions.
    skip_count : int
        Number of skipped compressions.
    total_files : int
        Total number of files processed.
    original_size : int
        Total original size in bytes.
    compressed_size : int
        Total compressed size in bytes.
    """

    success_count: int
    error_count: int
    skip_count: int
    total_files: int
    original_size: int
    compressed_size: int


class CompressionService:
    """Compression service for Host Image Backup.

    This class handles image compression operations including
    single file compression and batch compression with progress tracking.

    Parameters
    ----------
    config_manager : Any
        Configuration manager instance.
    """

    def __init__(self, config_manager: Any):
        """Initialize compression service."""
        self._config_manager = config_manager
        self._console = Console()
        self._logger = logger

    def compress_images(
        self,
        input_path: Path,
        output_dir: Path,
        quality: int = 85,
        output_format: str | None = None,
        recursive: bool = False,
        skip_existing: bool = True,
        verbose: bool = False,
    ) -> CompressionResult:
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
        CompressionResult
            Compression operation result.

        Raises
        ------
        Exception
            If compression operation fails.
        """
        try:
            # Create output directory
            FileUtils.ensure_directory_exists(output_dir)

            # Collect files to compress
            files_to_compress = self._collect_files_to_compress(input_path, recursive)

            if not files_to_compress:
                self._console.print("[yellow]No image files found to compress[/yellow]")
                return CompressionResult(0, 0, 0, 0, 0, 0)

            # Initialize counters
            success_count = 0
            error_count = 0
            skip_count = 0
            original_size = 0
            compressed_size = 0

            # Create progress bar
            with self._create_progress_bar() as progress:
                compress_task = progress.add_task(
                    "Compressing images",
                    total=len(files_to_compress),
                )

                # Process each file
                for file_path in files_to_compress:
                    try:
                        # Get original file size
                        file_original_size = FileUtils.get_file_size(file_path)
                        original_size += file_original_size

                        # Determine output file path
                        output_file = self._get_output_file_path(
                            file_path, input_path, output_dir, output_format
                        )

                        # Create output subdirectory if needed
                        FileUtils.ensure_directory_exists(output_file.parent)

                        # Skip if file exists and skip_existing is True
                        if skip_existing and output_file.exists():
                            skip_count += 1
                            compressed_size += FileUtils.get_file_size(output_file)
                            if verbose:
                                self._console.print(
                                    f"[yellow]Skipping existing file: {output_file}[/yellow]"
                                )
                            progress.update(compress_task, advance=1)
                            continue

                        # Compress image
                        if self._compress_single_image(
                            file_path, output_file, quality, output_format
                        ):
                            success_count += 1
                            compressed_size += FileUtils.get_file_size(output_file)
                            if verbose:
                                original_size_mb = file_original_size / (1024 * 1024)
                                compressed_size_mb = FileUtils.get_file_size(
                                    output_file
                                ) / (1024 * 1024)
                                savings = (
                                    1 - compressed_size_mb / original_size_mb
                                ) * 100
                                self._console.print(
                                    f"[green]Compressed: {file_path.name} -> {output_file.name} "
                                    f"({original_size_mb:.2f}MB -> {compressed_size_mb:.2f}MB, {savings:.1f}% saved)[/green]"
                                )
                        else:
                            error_count += 1
                            if verbose:
                                self._console.print(
                                    f"[red]Failed to compress: {file_path.name}[/red]"
                                )

                    except Exception as e:
                        error_count += 1
                        self._logger.error(f"Compression error for {file_path}: {e}")
                        if verbose:
                            self._console.print(
                                f"[red]Error compressing {file_path.name}: {e}[/red]"
                            )

                    progress.update(compress_task, advance=1)

            # Show summary
            self._console.print()
            self._show_compression_summary(
                success_count,
                error_count,
                skip_count,
                len(files_to_compress),
                original_size,
                compressed_size,
            )

            return CompressionResult(
                success_count=success_count,
                error_count=error_count,
                skip_count=skip_count,
                total_files=len(files_to_compress),
                original_size=original_size,
                compressed_size=compressed_size,
            )

        except Exception as e:
            self._logger.error(f"Compression process error: {e}")
            self._console.print(f"[red]Compression error: {str(e)}[/red]")
            raise

    def _collect_files_to_compress(
        self, input_path: Path, recursive: bool
    ) -> list[Path]:
        """Collect files to compress.

        Parameters
        ----------
        input_path : Path
            Input file or directory.
        recursive : bool
            Whether to search recursively.

        Returns
        -------
        list[Path]
            List of files to compress.
        """
        files_to_compress = []

        if input_path.is_file():
            if FileUtils.is_image_file(input_path):
                files_to_compress.append(input_path)
            else:
                self._console.print(f"[red]Unsupported file format: {input_path}[/red]")
        else:
            # Directory processing
            pattern = "**/*" if recursive else "*"
            for file_path in input_path.glob(pattern):
                if file_path.is_file() and FileUtils.is_image_file(file_path):
                    files_to_compress.append(file_path)

        return files_to_compress

    def _get_output_file_path(
        self,
        input_file: Path,
        input_path: Path,
        output_dir: Path,
        output_format: str | None,
    ) -> Path:
        """Get output file path for compression.

        Parameters
        ----------
        input_file : Path
            Input file path.
        input_path : Path
            Base input path.
        output_dir : Path
            Output directory.
        output_format : str, optional
            Output format.

        Returns
        -------
        Path
            Output file path.
        """
        # Determine relative path
        if input_path.is_dir():
            relative_path = input_file.relative_to(input_path)
        else:
            relative_path = Path(input_file.name)

        # Determine output format
        if output_format:
            output_ext = f".{output_format.lower()}"
        else:
            output_ext = input_file.suffix.lower()

        # For JPEG, use .jpg extension
        if output_ext == ".jpeg":
            output_ext = ".jpg"

        return output_dir / relative_path.with_suffix(output_ext)

    def _compress_single_image(
        self,
        input_file: Path,
        output_file: Path,
        quality: int,
        output_format: str | None,
    ) -> bool:
        """Compress a single image file.

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
            True if compression successful, False otherwise.
        """
        try:
            from PIL import Image

            # Open image
            with Image.open(input_file) as img:
                # Convert RGBA to RGB for JPEG format
                if (
                    (output_format and output_format.upper() == "JPEG")
                    or (
                        not output_format
                        and input_file.suffix.lower() in [".png", ".webp"]
                    )
                ) and img.mode in ("RGBA", "LA", "P"):
                    # Create white background for transparency
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(
                        img, mask=img.split()[-1] if img.mode == "RGBA" else None
                    )
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
            self._logger.error(f"Failed to compress {input_file}: {e}")
            return False

    def _create_progress_bar(self):
        """Create progress bar with consistent styling.

        Returns
        -------
        Progress
            Rich progress bar context manager.
        """
        from ..config.styles import create_backup_progress_bar

        return create_backup_progress_bar()

    def _show_compression_summary(
        self,
        success: int,
        error: int,
        skip: int,
        total: int,
        original_size: int,
        compressed_size: int,
    ) -> None:
        """Show compression summary.

        Parameters
        ----------
        success : int
            Number of successful compressions.
        error : int
            Number of failed compressions.
        skip : int
            Number of skipped compressions.
        total : int
            Total number of files.
        original_size : int
            Total original size in bytes.
        compressed_size : int
            Total compressed size in bytes.
        """
        from ..config.styles import print_compression_summary

        print_compression_summary(success, error, skip, total)

    def validate_compression_requirements(
        self, input_path: Path, output_dir: Path
    ) -> bool:
        """Validate compression requirements.

        Parameters
        ----------
        input_path : Path
            Input file or directory.
        output_dir : Path
            Output directory.

        Returns
        -------
        bool
            True if requirements are met, False otherwise.
        """
        # Check if input exists
        if not input_path.exists():
            self._console.print(f"[red]Input path does not exist: {input_path}[/red]")
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

        # Check if PIL is available
        try:
            import importlib.util

            if importlib.util.find_spec("PIL.Image") is None:
                self._console.print(
                    "[red]PIL (Pillow) is required for image compression[/red]"
                )
                return False
        except ImportError:
            self._console.print(
                "[red]PIL (Pillow) is required for image compression[/red]"
            )
            return False

        return True

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
        Dict[str, Any] or None
            Estimated compression savings, or None if cannot estimate.
        """
        try:
            # Collect files to compress
            files_to_compress = self._collect_files_to_compress(
                input_path, recursive=True
            )

            if not files_to_compress:
                return None

            # Calculate total original size
            original_size = sum(
                FileUtils.get_file_size(file_path) for file_path in files_to_compress
            )

            # Estimate compression ratio (conservative: 30% savings for JPEG, 20% for PNG)
            estimated_ratio = 0.7  # 30% savings
            compressed_size = int(original_size * estimated_ratio)

            return {
                "total_files": len(files_to_compress),
                "original_size": original_size,
                "compressed_size": compressed_size,
                "savings": original_size - compressed_size,
                "savings_percentage": (1 - compressed_size / original_size) * 100,
                "formatted_original_size": FileUtils.format_file_size(original_size),
                "formatted_compressed_size": FileUtils.format_file_size(
                    compressed_size
                ),
                "formatted_savings": FileUtils.format_file_size(
                    original_size - compressed_size
                ),
            }
        except Exception:
            return None

    def get_supported_formats(self) -> list[str]:
        """Get list of supported image formats.

        Returns
        -------
        list[str]
            List of supported image formats.
        """
        return list(SUPPORTED_IMAGE_EXTENSIONS)

    def get_optimal_quality(self, file_path: Path, target_size_mb: float) -> int | None:
        """Get optimal quality for target file size.

        Parameters
        ----------
        file_path : Path
            Image file path.
        target_size_mb : float
            Target file size in MB.

        Returns
        -------
        int or None
            Optimal quality (1-100), or None if cannot determine.
        """
        try:
            from PIL import Image

            # Get original file size
            original_size = FileUtils.get_file_size(file_path)
            target_size_bytes = int(target_size_mb * 1024 * 1024)

            # If already smaller than target, return 100 (best quality)
            if original_size <= target_size_bytes:
                return 100

            # Binary search for optimal quality
            low, high = 1, 100
            best_quality = 1

            while low <= high:
                mid = (low + high) // 2

                # Test compression with mid quality
                test_file = Path(f"/tmp/test_compression_{mid}.jpg")
                try:
                    with Image.open(file_path) as img:
                        img.save(test_file, format="JPEG", quality=mid, optimize=True)

                    compressed_size = FileUtils.get_file_size(test_file)

                    if compressed_size <= target_size_bytes:
                        best_quality = mid
                        low = mid + 1
                    else:
                        high = mid - 1
                finally:
                    if test_file.exists():
                        test_file.unlink()

            return best_quality
        except Exception:
            return None
