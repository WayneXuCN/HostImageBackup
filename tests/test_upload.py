from unittest.mock import Mock, patch

import pytest

from host_image_backup.config import AppConfig, OSSConfig
from host_image_backup.metadata import MetadataManager
from host_image_backup.providers.base import UploadResult
from host_image_backup.service import BackupService


class TestMetadataManager:
    """Test metadata management functionality"""

    def test_init_database(self, tmp_path):
        """Test database initialization"""
        db_path = tmp_path / "test.db"
        manager = MetadataManager(db_path)

        # Database should be created
        assert db_path.exists()

        # Tables should exist
        import sqlite3

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            assert "backup_records" in tables
            assert "image_metadata" in tables

    def test_get_file_hash(self, tmp_path):
        """Test file hash calculation"""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        manager = MetadataManager()
        hash_value = manager.get_file_hash(test_file)

        # Should be SHA256 hash of "Hello, World!"
        expected_hash = (
            "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        )
        assert hash_value == expected_hash

    def test_record_backup(self, tmp_path):
        """Test recording backup operations"""
        db_path = tmp_path / "test.db"
        manager = MetadataManager(db_path)

        test_file = tmp_path / "test.jpg"
        test_file.write_text("fake image data")

        record_id = manager.record_backup(
            operation="upload",
            provider="oss",
            file_path=test_file,
            remote_path="images/test.jpg",
            file_hash="abc123",
            file_size=100,
            status="success",
            message="Upload successful",
        )

        assert record_id > 0

        # Verify record was saved
        records = manager.get_backup_records()
        assert len(records) == 1
        assert records[0].operation == "upload"
        assert records[0].provider == "oss"
        assert records[0].status == "success"

    def test_get_statistics(self, tmp_path):
        """Test statistics generation"""
        db_path = tmp_path / "test.db"
        manager = MetadataManager(db_path)

        test_file = tmp_path / "test.jpg"
        test_file.write_text("fake image data")

        # Record some operations
        manager.record_backup(
            operation="upload",
            provider="oss",
            file_path=test_file,
            remote_path="images/test.jpg",
            file_hash="abc123",
            file_size=100,
            status="success",
        )

        manager.record_backup(
            operation="download",
            provider="oss",
            file_path=test_file,
            remote_path="images/test.jpg",
            file_hash="abc123",
            file_size=100,
            status="failed",
        )

        stats = manager.get_statistics()

        assert stats["total_operations"] == 2
        assert stats["successful_operations"] == 1
        assert stats["failed_operations"] == 1
        assert stats["operations_by_type"]["upload"] == 1
        assert stats["operations_by_type"]["download"] == 1

    def test_find_duplicates(self, tmp_path):
        """Test duplicate file detection"""
        db_path = tmp_path / "test.db"
        manager = MetadataManager(db_path)

        test_file1 = tmp_path / "test1.jpg"
        test_file2 = tmp_path / "test2.jpg"
        test_file1.write_text("same content")
        test_file2.write_text("same content")

        # Update metadata for both files (same hash)
        hash_value = manager.get_file_hash(test_file1)
        manager.update_file_metadata(
            file_path=test_file1, file_hash=hash_value, file_size=100
        )
        manager.update_file_metadata(
            file_path=test_file2, file_hash=hash_value, file_size=100
        )

        duplicates = manager.find_duplicates()
        assert len(duplicates) == 1
        assert hash_value in duplicates
        assert len(duplicates[hash_value]) == 2


class TestBackupServiceUpload:
    """Test backup service upload functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.config = AppConfig()
        self.oss_config = OSSConfig(
            name="oss",
            enabled=True,
            access_key_id="test_key",
            access_key_secret="test_secret",
            bucket="test-bucket",
            endpoint="oss-test.aliyuncs.com",
        )
        self.config.providers = {"oss": self.oss_config}

        self.service = BackupService(self.config)

    @patch("host_image_backup.service.MetadataManager")
    def test_upload_image_success(self, mock_metadata_manager, tmp_path):
        """Test successful image upload"""
        # Mock metadata manager
        mock_metadata_manager.return_value.get_file_hash.return_value = "abc123"

        # Create test file
        test_file = tmp_path / "test.jpg"
        test_file.write_text("fake image data")

        # Mock provider
        mock_provider = Mock()
        mock_provider.upload_image.return_value = UploadResult(
            success=True,
            url="https://test-bucket.oss-test.aliyuncs.com/test.jpg",
            message="Upload successful",
        )

        with (
            patch.object(self.service, "get_provider", return_value=mock_provider),
            patch.object(
                self.service, "metadata_manager", mock_metadata_manager.return_value
            ),
        ):
            result = self.service.upload_image(
                provider_name="oss", file_path=test_file, verbose=False
            )

        assert result is True
        mock_provider.upload_image.assert_called_once()

        # Verify metadata was recorded
        mock_metadata_manager.return_value.record_backup.assert_called_once()

    @patch("host_image_backup.service.MetadataManager")
    def test_upload_image_failure(self, mock_metadata_manager, tmp_path):
        """Test failed image upload"""
        # Mock metadata manager
        mock_metadata_manager.return_value.get_file_hash.return_value = "abc123"

        # Create test file
        test_file = tmp_path / "test.jpg"
        test_file.write_text("fake image data")

        # Mock provider
        mock_provider = Mock()
        mock_provider.upload_image.return_value = UploadResult(
            success=False, message="Upload failed: network error"
        )

        with (
            patch.object(self.service, "get_provider", return_value=mock_provider),
            patch.object(
                self.service, "metadata_manager", mock_metadata_manager.return_value
            ),
        ):
            result = self.service.upload_image(
                provider_name="oss", file_path=test_file, verbose=False
            )

        assert result is False
        mock_provider.upload_image.assert_called_once()

        # Verify failure was recorded
        mock_metadata_manager.return_value.record_backup.assert_called_once()

    def test_upload_batch_success(self, tmp_path):
        """Test successful batch upload"""
        # Create test files
        test_files = []
        for i in range(3):
            test_file = tmp_path / f"test{i}.jpg"
            test_file.write_text(f"fake image data {i}")
            test_files.append(test_file)

        # Mock provider
        mock_provider = Mock()
        mock_provider.upload_image.return_value = UploadResult(
            success=True,
            url="https://test-bucket.oss-test.aliyuncs.com/test.jpg",
            message="Upload successful",
        )

        with (
            patch.object(self.service, "get_provider", return_value=mock_provider),
            patch.object(
                self.service, "upload_image", Mock(return_value=True)
            ) as mock_upload_image,
        ):
            result = self.service.upload_batch(
                provider_name="oss", file_paths=test_files, verbose=False
            )

        assert result is True
        assert mock_upload_image.call_count == 3


class TestProviderUpload:
    """Test provider upload functionality"""

    def test_oss_provider_upload_structure(self):
        """Test OSS provider has required upload methods"""
        from host_image_backup.config import OSSConfig
        from host_image_backup.providers.oss import OSSProvider

        config = OSSConfig(
            name="oss",
            enabled=True,
            access_key_id="test",
            access_key_secret="test",
            bucket="test",
            endpoint="test.com",
        )

        provider = OSSProvider(config)

        # Check that upload methods exist
        assert hasattr(provider, "upload_image")
        assert hasattr(provider, "get_file_info")
        assert hasattr(provider, "delete_image")

        # Check method signatures
        import inspect

        upload_sig = inspect.signature(provider.upload_image)
        assert "file_path" in upload_sig.parameters
        assert "remote_path" in upload_sig.parameters

    def test_cos_provider_upload_structure(self):
        """Test COS provider has required upload methods"""
        from host_image_backup.config import COSConfig
        from host_image_backup.providers.cos import COSProvider

        config = COSConfig(
            name="cos",
            enabled=True,
            secret_id="test",
            secret_key="test",
            bucket="test",
            region="test",
        )

        provider = COSProvider(config)

        # Check that upload methods exist
        assert hasattr(provider, "upload_image")
        assert hasattr(provider, "get_file_info")
        assert hasattr(provider, "delete_image")

        # Check method signatures
        import inspect

        upload_sig = inspect.signature(provider.upload_image)
        assert "file_path" in upload_sig.parameters
        assert "remote_path" in upload_sig.parameters


if __name__ == "__main__":
    pytest.main([__file__])
