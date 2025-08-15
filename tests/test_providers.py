"""Test providers module."""

from src.host_image_backup.providers import (
    SUPPORTED_IMAGE_EXTENSIONS,
    BaseProvider,
    COSProvider,
    GitHubProvider,
    ImageInfo,
    ImgurProvider,
    OSSProvider,
    SMSProvider,
)


class TestImageInfo:
    """Test ImageInfo dataclass."""

    def test_image_info_creation(self):
        """Test creating ImageInfo instance."""
        image_info = ImageInfo(
            url="https://example.com/image.jpg", filename="image.jpg"
        )
        assert image_info.url == "https://example.com/image.jpg"
        assert image_info.filename == "image.jpg"
        assert image_info.size is None
        assert image_info.created_at is None
        assert image_info.tags is None
        assert image_info.metadata is None

    def test_image_info_with_metadata(self):
        """Test creating ImageInfo with metadata."""
        metadata = {"hash": "abc123", "type": "image/jpeg"}
        image_info = ImageInfo(
            url="https://example.com/image.jpg",
            filename="image.jpg",
            size=1024,
            created_at="2023-01-01T00:00:00Z",
            tags=["photo", "landscape"],
            metadata=metadata,
        )
        assert image_info.size == 1024
        assert image_info.created_at == "2023-01-01T00:00:00Z"
        assert image_info.tags == ["photo", "landscape"]
        assert image_info.metadata == metadata


class TestSupportedExtensions:
    """Test supported image extensions constant."""

    def test_supported_extensions_type(self):
        """Test that SUPPORTED_IMAGE_EXTENSIONS is a set."""
        assert isinstance(SUPPORTED_IMAGE_EXTENSIONS, set)

    def test_supported_extensions_content(self):
        """Test that common image extensions are included."""
        expected_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        assert expected_extensions.issubset(SUPPORTED_IMAGE_EXTENSIONS)

    def test_extensions_lowercase(self):
        """Test that all extensions are lowercase."""
        for ext in SUPPORTED_IMAGE_EXTENSIONS:
            assert ext.islower(), f"Extension {ext} should be lowercase"

    def test_extensions_start_with_dot(self):
        """Test that all extensions start with a dot."""
        for ext in SUPPORTED_IMAGE_EXTENSIONS:
            assert ext.startswith("."), f"Extension {ext} should start with a dot"


class TestProviderImports:
    """Test that all providers can be imported correctly."""

    def test_base_provider_import(self):
        """Test BaseProvider import."""
        assert BaseProvider is not None
        assert hasattr(BaseProvider, "test_connection")
        assert hasattr(BaseProvider, "list_images")
        assert hasattr(BaseProvider, "download_image")

    def test_oss_provider_import(self):
        """Test OSSProvider import."""
        assert OSSProvider is not None
        assert issubclass(OSSProvider, BaseProvider)

    def test_cos_provider_import(self):
        """Test COSProvider import."""
        assert COSProvider is not None
        assert issubclass(COSProvider, BaseProvider)

    def test_sms_provider_import(self):
        """Test SMSProvider import."""
        assert SMSProvider is not None
        assert issubclass(SMSProvider, BaseProvider)

    def test_imgur_provider_import(self):
        """Test ImgurProvider import."""
        assert ImgurProvider is not None
        assert issubclass(ImgurProvider, BaseProvider)

    def test_github_provider_import(self):
        """Test GitHubProvider import."""
        assert GitHubProvider is not None
        assert issubclass(GitHubProvider, BaseProvider)
