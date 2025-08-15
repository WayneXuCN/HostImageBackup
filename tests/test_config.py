"""Test configuration module."""

import pytest

from src.host_image_backup.config import (
    AppConfig,
    COSConfig,
    GitHubConfig,
    ImgurConfig,
    OSSConfig,
    SMSConfig,
)


class TestProviderConfigs:
    """Test provider configuration classes."""

    def test_oss_config_validation(self):
        """Test OSS configuration validation."""
        # Valid configuration
        valid_config = OSSConfig(
            name="oss",
            access_key_id="test_key",
            access_key_secret="test_secret",
            bucket="test_bucket",
            endpoint="oss-cn-hangzhou.aliyuncs.com",
        )
        assert valid_config.validate_config() is True

        # Invalid configuration - missing fields
        invalid_config = OSSConfig(name="oss")
        assert invalid_config.validate_config() is False

        # Invalid configuration - empty strings
        empty_config = OSSConfig(
            name="oss", access_key_id="", access_key_secret="", bucket="", endpoint=""
        )
        assert empty_config.validate_config() is False

    def test_cos_config_validation(self):
        """Test COS configuration validation."""
        # Valid configuration
        valid_config = COSConfig(
            name="cos",
            secret_id="test_id",
            secret_key="test_key",
            bucket="test_bucket",
            region="ap-guangzhou",
        )
        assert valid_config.validate_config() is True

        # Invalid configuration
        invalid_config = COSConfig(name="cos")
        assert invalid_config.validate_config() is False

    def test_sms_config_validation(self):
        """Test SM.MS configuration validation."""
        # Valid configuration
        valid_config = SMSConfig(name="sms", api_token="test_token")
        assert valid_config.validate_config() is True

        # Invalid configuration
        invalid_config = SMSConfig(name="sms")
        assert invalid_config.validate_config() is False

    def test_imgur_config_validation(self):
        """Test Imgur configuration validation."""
        # Valid configuration
        valid_config = ImgurConfig(
            name="imgur",
            client_id="test_id",
            client_secret="test_secret",
            access_token="test_token",
        )
        assert valid_config.validate_config() is True

        # Invalid configuration
        invalid_config = ImgurConfig(name="imgur")
        assert invalid_config.validate_config() is False

    def test_github_config_validation(self):
        """Test GitHub configuration validation."""
        # Valid configuration
        valid_config = GitHubConfig(
            name="github", token="ghp_test_token", owner="test_owner", repo="test_repo"
        )
        assert valid_config.validate_config() is True

        # Invalid configuration
        invalid_config = GitHubConfig(name="github")
        assert invalid_config.validate_config() is False


class TestAppConfig:
    """Test application configuration."""

    def test_app_config_defaults(self):
        """Test default application configuration values."""
        config = AppConfig()
        assert config.default_output_dir == "./backup"
        assert config.max_concurrent_downloads == 5
        assert config.timeout == 30
        assert config.retry_count == 3
        assert config.chunk_size == 8192
        assert config.log_level == "INFO"
        assert config.providers == {}

    def test_log_level_validation(self):
        """Test log level validation."""
        # Valid log levels
        valid_levels = [
            "TRACE",
            "DEBUG",
            "INFO",
            "SUCCESS",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ]
        for level in valid_levels:
            config = AppConfig(log_level=level)
            assert config.log_level == level

        # Case insensitive
        config = AppConfig(log_level="debug")
        assert config.log_level == "DEBUG"

        # Invalid log level should raise ValueError
        with pytest.raises(ValueError):
            AppConfig(log_level="INVALID")

    def test_constraints(self):
        """Test configuration constraints."""
        # Valid ranges
        config = AppConfig(
            max_concurrent_downloads=10, timeout=60, retry_count=5, chunk_size=4096
        )
        assert config.max_concurrent_downloads == 10
        assert config.timeout == 60
        assert config.retry_count == 5
        assert config.chunk_size == 4096

        # Test boundary values
        config = AppConfig(max_concurrent_downloads=1)  # minimum
        assert config.max_concurrent_downloads == 1

        config = AppConfig(max_concurrent_downloads=20)  # maximum
        assert config.max_concurrent_downloads == 20
