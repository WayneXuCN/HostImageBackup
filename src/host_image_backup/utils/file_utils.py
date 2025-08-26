import hashlib
from pathlib import Path


class FileUtils:
    """File utility class for Host Image Backup.

    This class provides static methods for file operations
    including filename sanitization, hash calculation, and path handling.
    """

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename by removing illegal characters.

        Parameters
        ----------
        filename : str
            Original filename.

        Returns
        -------
        str
            Sanitized filename.

        Examples
        --------
        >>> FileUtils.sanitize_filename("file*name?.jpg")
        'file_name_.jpg'
        """
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

    @staticmethod
    def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
        """Calculate file hash.

        Parameters
        ----------
        file_path : Path
            Path to the file.
        algorithm : str, default="sha256"
            Hash algorithm to use (sha256, md5, sha1, etc.).

        Returns
        -------
        str
            File hash as hexadecimal string.

        Raises
        ------
        FileNotFoundError
            If file doesn't exist.
        ValueError
            If algorithm is not supported.

        Examples
        --------
        >>> hash_value = FileUtils.calculate_file_hash(Path("image.jpg"))
        >>> len(hash_value)
        64
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Create hash object
        if algorithm.lower() == "sha256":
            hash_obj = hashlib.sha256()
        elif algorithm.lower() == "md5":
            hash_obj = hashlib.md5()
        elif algorithm.lower() == "sha1":
            hash_obj = hashlib.sha1()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

        # Calculate hash
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)

        return hash_obj.hexdigest()

    @staticmethod
    def get_file_size(file_path: Path) -> int:
        """Get file size in bytes.

        Parameters
        ----------
        file_path : Path
            Path to the file.

        Returns
        -------
        int
            File size in bytes.

        Raises
        ------
        FileNotFoundError
            If file doesn't exist.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path.stat().st_size

    @staticmethod
    def ensure_directory_exists(directory: Path) -> None:
        """Ensure directory exists, create if necessary.

        Parameters
        ----------
        directory : Path
            Directory path to ensure exists.

        Raises
        ------
        OSError
            If directory cannot be created.
        """
        directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_unique_filename(file_path: Path) -> Path:
        """Get unique filename by adding suffix if file exists.

        Parameters
        ----------
        file_path : Path
            Desired file path.

        Returns
        -------
        Path
            Unique file path.

        Examples
        --------
        >>> # If file.txt exists, returns file_1.txt
        >>> unique_path = FileUtils.get_unique_filename(Path("file.txt"))
        """
        if not file_path.exists():
            return file_path

        stem = file_path.stem
        suffix = file_path.suffix
        parent = file_path.parent

        counter = 1
        while True:
            new_filename = f"{stem}_{counter}{suffix}"
            new_path = parent / new_filename
            if not new_path.exists():
                return new_path
            counter += 1

    @staticmethod
    def is_image_file(file_path: Path) -> bool:
        """Check if file is an image based on extension.

        Parameters
        ----------
        file_path : Path
            Path to the file.

        Returns
        -------
        bool
            True if file is an image, False otherwise.
        """
        image_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".webp",
            ".svg",
            ".tiff",
            ".tif",
            ".ico",
        }
        return file_path.suffix.lower() in image_extensions

    @staticmethod
    def get_relative_path(file_path: Path, base_path: Path) -> Path:
        """Get relative path from base path.

        Parameters
        ----------
        file_path : Path
            File path.
        base_path : Path
            Base path.

        Returns
        -------
        Path
            Relative path.

        Raises
        ------
        ValueError
            If file_path is not under base_path.
        """
        try:
            return file_path.relative_to(base_path)
        except ValueError as err:
            raise ValueError(
                f"File {file_path} is not under base path {base_path}"
            ) from err

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human-readable format.

        Parameters
        ----------
        size_bytes : int
            File size in bytes.

        Returns
        -------
        str
            Formatted file size.

        Examples
        --------
        >>> FileUtils.format_file_size(1024)
        '1.00 KB'
        >>> FileUtils.format_file_size(1048576)
        '1.00 MB'
        """
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1

        return f"{size:.2f} {size_names[i]}"

    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """Get safe filename by removing or replacing problematic characters.

        This is more aggressive than sanitize_filename and ensures
        the filename is safe for all filesystems.

        Parameters
        ----------
        filename : str
            Original filename.

        Returns
        -------
        str
            Safe filename.
        """
        # Remove or replace problematic characters
        unsafe_chars = "<>:\"/\\|?*'`!@#$%^&+="
        safe_chars = "_"

        for char in unsafe_chars:
            filename = filename.replace(char, safe_chars)

        # Remove leading/trailing whitespace and dots
        filename = filename.strip(". ")

        # Replace multiple consecutive underscores with single underscore
        while "__" in filename:
            filename = filename.replace("__", "_")

        # Remove leading/trailing underscores
        filename = filename.strip("_")

        # Ensure filename is not empty
        if not filename:
            filename = "unnamed_file"

        # Limit length
        if len(filename) > 200:
            name, ext = Path(filename).stem, Path(filename).suffix
            max_name_length = 200 - len(ext)
            if max_name_length > 0:
                filename = name[:max_name_length] + ext
            else:
                filename = name[:200]

        return filename

    @staticmethod
    def copy_file_with_hash_check(source: Path, destination: Path) -> bool:
        """Copy file with hash verification.

        Parameters
        ----------
        source : Path
            Source file path.
        destination : Path
            Destination file path.

        Returns
        -------
        bool
            True if copy successful and hashes match, False otherwise.
        """
        try:
            # Calculate source hash
            source_hash = FileUtils.calculate_file_hash(source)

            # Copy file
            import shutil

            shutil.copy2(source, destination)

            # Verify hash
            dest_hash = FileUtils.calculate_file_hash(destination)

            return source_hash == dest_hash
        except Exception:
            return False

    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get file extension in lowercase.

        Parameters
        ----------
        filename : str
            Filename.

        Returns
        -------
        str
            File extension in lowercase (including dot).

        Examples
        --------
        >>> FileUtils.get_file_extension("image.JPG")
        '.jpg'
        """
        return Path(filename).suffix.lower()

    @staticmethod
    def change_extension(filename: str, new_extension: str) -> str:
        """Change file extension.

        Parameters
        ----------
        filename : str
            Original filename.
        new_extension : str
            New extension (with or without dot).

        Returns
        -------
        str
            Filename with new extension.

        Examples
        --------
        >>> FileUtils.change_extension("image.png", ".jpg")
        'image.jpg'
        >>> FileUtils.change_extension("image.png", "jpg")
        'image.jpg'
        """
        # Ensure new_extension starts with dot
        if not new_extension.startswith("."):
            new_extension = "." + new_extension

        path = Path(filename)
        return path.with_suffix(new_extension).name
