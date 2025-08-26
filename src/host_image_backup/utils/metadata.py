import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class BackupRecord:
    """Backup operation record

    Parameters
    ----------
    id : int
        Record ID.
    operation : str
        Operation type (upload/download/sync).
    provider : str
        Provider name.
    file_path : str
        Local file path.
    remote_path : str
        Remote file path.
    file_hash : str
        File hash.
    file_size : int
        File size in bytes.
    status : str
        Operation status (success/failed).
    message : str, optional
        Status message.
    created_at : datetime
        Record creation time.
    metadata : dict, optional
        Additional metadata.
    """

    id: int
    operation: str
    provider: str
    file_path: str
    remote_path: str
    file_hash: str
    file_size: int
    status: str
    message: str | None = None
    created_at: datetime | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class ImageMetadata:
    """Image metadata

    Parameters
    ----------
    id : int
        Metadata ID.
    file_path : str
        File path.
    file_hash : str
        File hash.
    file_size : int
        File size in bytes.
    width : int, optional
        Image width.
    height : int, optional
        Image height.
    format : str, optional
        Image format.
    exif_data : dict, optional
        EXIF data.
    created_at : datetime
        Metadata creation time.
    updated_at : datetime
        Last update time.
    """

    id: int
    file_path: str
    file_hash: str
    file_size: int
    width: int | None = None
    height: int | None = None
    format: str | None = None
    exif_data: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MetadataManager:
    """Metadata management for backup operations"""

    def __init__(self, db_path: Path | None = None):
        """Initialize metadata manager

        Parameters
        ----------
        db_path : Path, optional
            Database file path. If None, uses default location.
        """
        if db_path is None:
            # Default database location
            app_data_dir = Path.home() / ".config" / "host-image-backup"
            app_data_dir.mkdir(parents=True, exist_ok=True)
            db_path = app_data_dir / "metadata.db"

        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backup_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    remote_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS image_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_hash TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    width INTEGER,
                    height INTEGER,
                    format TEXT,
                    exif_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_backup_records_file_hash
                ON backup_records(file_hash)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_backup_records_operation
                ON backup_records(operation)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_image_metadata_file_hash
                ON image_metadata(file_hash)
            """)

            conn.commit()

    def get_file_hash(self, file_path: Path) -> str:
        """Calculate file hash

        Parameters
        ----------
        file_path : Path
            File path.

        Returns
        -------
        str
            File hash (SHA256).
        """
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def record_backup(
        self,
        operation: str,
        provider: str,
        file_path: Path,
        remote_path: str,
        file_hash: str,
        file_size: int,
        status: str,
        message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Record backup operation

        Parameters
        ----------
        operation : str
            Operation type.
        provider : str
            Provider name.
        file_path : Path
            Local file path.
        remote_path : str
            Remote file path.
        file_hash : str
            File hash.
        file_size : int
            File size.
        status : str
            Operation status.
        message : str, optional
            Status message.
        metadata : dict, optional
            Additional metadata.

        Returns
        -------
        int
            Record ID.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO backup_records
                (operation, provider, file_path, remote_path, file_hash, file_size, status, message, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    operation,
                    provider,
                    str(file_path),
                    remote_path,
                    file_hash,
                    file_size,
                    status,
                    message,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            conn.commit()
            if cursor.lastrowid is None:
                raise RuntimeError("Failed to insert record, lastrowid not generated")
            return cursor.lastrowid

    def get_backup_records(
        self,
        operation: str | None = None,
        provider: str | None = None,
        limit: int | None = None,
    ) -> list[BackupRecord]:
        """Get backup records

        Parameters
        ----------
        operation : str, optional
            Filter by operation type.
        provider : str, optional
            Filter by provider.
        limit : int, optional
            Limit number of records.

        Returns
        -------
        list[BackupRecord]
            List of backup records.
        """
        query = "SELECT * FROM backup_records WHERE 1=1"
        params = []

        if operation:
            query += " AND operation = ?"
            params.append(operation)

        if provider:
            query += " AND provider = ?"
            params.append(provider)

        query += " ORDER BY created_at DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        records = []
        for row in rows:
            metadata = json.loads(row["metadata"]) if row["metadata"] else None
            records.append(
                BackupRecord(
                    id=row["id"],
                    operation=row["operation"],
                    provider=row["provider"],
                    file_path=row["file_path"],
                    remote_path=row["remote_path"],
                    file_hash=row["file_hash"],
                    file_size=row["file_size"],
                    status=row["status"],
                    message=row["message"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    metadata=metadata,
                )
            )

        return records

    def get_file_metadata(self, file_path: Path) -> ImageMetadata | None:
        """Get file metadata

        Parameters
        ----------
        file_path : Path
            File path.

        Returns
        -------
        ImageMetadata or None
            File metadata, or None if not found.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM image_metadata WHERE file_path = ?
            """,
                (str(file_path),),
            )
            row = cursor.fetchone()

        if not row:
            return None

        exif_data = json.loads(row["exif_data"]) if row["exif_data"] else None
        return ImageMetadata(
            id=row["id"],
            file_path=row["file_path"],
            file_hash=row["file_hash"],
            file_size=row["file_size"],
            width=row["width"],
            height=row["height"],
            format=row["format"],
            exif_data=exif_data,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def update_file_metadata(
        self,
        file_path: Path,
        file_hash: str,
        file_size: int,
        width: int | None = None,
        height: int | None = None,
        format: str | None = None,
        exif_data: dict[str, Any] | None = None,
    ) -> int:
        """Update file metadata

        Parameters
        ----------
        file_path : Path
            File path.
        file_hash : str
            File hash.
        file_size : int
            File size.
        width : int, optional
            Image width.
        height : int, optional
            Image height.
        format : str, optional
            Image format.
        exif_data : dict, optional
            EXIF data.

        Returns
        -------
        int
            Metadata ID.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO image_metadata
                (file_path, file_hash, file_size, width, height, format, exif_data, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    str(file_path),
                    file_hash,
                    file_size,
                    width,
                    height,
                    format,
                    json.dumps(exif_data) if exif_data else None,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            if cursor.lastrowid is None:
                raise RuntimeError(
                    "Failed to insert/update metadata, lastrowid not generated"
                )
            return cursor.lastrowid

    def find_duplicates(self) -> dict[str, list[str]]:
        """Find duplicate files by hash

        Returns
        -------
        dict[str, list[str]]
            Dictionary mapping file hash to list of file paths.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT file_hash, GROUP_CONCAT(file_path) as files
                FROM image_metadata
                GROUP BY file_hash
                HAVING COUNT(*) > 1
            """)
            rows = cursor.fetchall()

        duplicates = {}
        for row in rows:
            file_hash = row[0]
            file_paths = row[1].split(",")
            duplicates[file_hash] = file_paths

        return duplicates

    def get_statistics(self) -> dict[str, Any]:
        """Get backup statistics

        Returns
        -------
        dict[str, Any]
            Statistics dictionary.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total backup operations
            cursor.execute("SELECT COUNT(*) FROM backup_records")
            total_operations = cursor.fetchone()[0]

            # Successful operations
            cursor.execute(
                "SELECT COUNT(*) FROM backup_records WHERE status = 'success'"
            )
            successful_operations = cursor.fetchone()[0]

            # Failed operations
            cursor.execute(
                "SELECT COUNT(*) FROM backup_records WHERE status = 'failed'"
            )
            failed_operations = cursor.fetchone()[0]

            # Total files
            cursor.execute("SELECT COUNT(*) FROM image_metadata")
            total_files = cursor.fetchone()[0]

            # Total file size
            cursor.execute("SELECT SUM(file_size) FROM image_metadata")
            total_size = cursor.fetchone()[0] or 0

            # Operations by type
            cursor.execute("""
                SELECT operation, COUNT(*)
                FROM backup_records
                GROUP BY operation
            """)
            operations_by_type = dict(cursor.fetchall())

        return {
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "total_files": total_files,
            "total_size": total_size,
            "operations_by_type": operations_by_type,
        }
