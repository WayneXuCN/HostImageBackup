from typing import Any


class HostImageBackupError(Exception):
    """Base exception class for all host image backup errors.

    Parameters
    ----------
    message : str
        The error message.
    code : str, optional
        Error code for programmatic handling.
    details : Any, optional
        Additional error details.

    Examples
    --------
    >>> raise HostImageBackupError("Something went wrong")
    """

    def __init__(
        self, message: str, code: str | None = None, details: Any | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class ConfigurationError(HostImageBackupError):
    """Raised when there's an error in configuration.

    This exception is raised when configuration validation fails
    or when required configuration parameters are missing.

    Examples
    --------
    >>> raise ConfigurationError("Missing API key", code="MISSING_API_KEY")
    """

    pass


class ProviderError(HostImageBackupError):
    """Base exception for provider-related errors.

    This exception is raised when there's an error specific to
    image hosting providers.

    Examples
    --------
    >>> raise ProviderError("Provider connection failed", code="CONNECTION_FAILED")
    """

    pass


class AuthenticationError(ProviderError):
    """Raised when provider authentication fails.

    This exception indicates that the provided credentials
    are invalid or expired.

    Examples
    --------
    >>> raise AuthenticationError("Invalid API token", code="INVALID_TOKEN")
    """

    pass


class ConnectionError(ProviderError):
    """Raised when connection to provider fails.

    This exception indicates network-related issues or
    when the provider service is unavailable.

    Examples
    --------
    >>> raise ConnectionError("Failed to connect to provider", code="NETWORK_ERROR")
    """

    pass


class ProviderAPIError(ProviderError):
    """Raised when provider API returns an error.

    Parameters
    ----------
    message : str
        The error message.
    status_code : int, optional
        HTTP status code from the API response.
    response_data : Any, optional
        Response data from the API.

    Examples
    --------
    >>> raise ProviderAPIError("API rate limit exceeded", status_code=429)
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: Any | None = None,
        **kwargs,
    ) -> None:
        super().__init__(message, **kwargs)
        self.status_code = status_code
        self.response_data = response_data


class DownloadError(HostImageBackupError):
    """Raised when file download fails.

    This exception is raised when there's an error downloading
    images from providers.

    Parameters
    ----------
    message : str
        The error message.
    url : str, optional
        The URL that failed to download.
    filename : str, optional
        The filename that failed to download.

    Examples
    --------
    >>> raise DownloadError("Download failed", url="https://example.com/image.jpg")
    """

    def __init__(
        self,
        message: str,
        url: str | None = None,
        filename: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(message, **kwargs)
        self.url = url
        self.filename = filename


class FileSystemError(HostImageBackupError):
    """Raised when file system operations fail.

    This exception is raised when there are issues with
    file system operations like creating directories,
    writing files, etc.

    Examples
    --------
    >>> raise FileSystemError("Permission denied", code="PERMISSION_DENIED")
    """

    pass


class ValidationError(HostImageBackupError):
    """Raised when data validation fails.

    This exception is raised when input data doesn't
    meet the expected format or constraints.

    Examples
    --------
    >>> raise ValidationError("Invalid file format", code="INVALID_FORMAT")
    """

    pass


class RetryableError(HostImageBackupError):
    """Base class for errors that can be retried.

    This exception indicates that the operation might succeed
    if retried after some time.

    Parameters
    ----------
    message : str
        The error message.
    retry_after : int, optional
        Suggested retry delay in seconds.

    Examples
    --------
    >>> raise RetryableError("Temporary service unavailable", retry_after=60)
    """

    def __init__(self, message: str, retry_after: int | None = None, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class RateLimitError(RetryableError):
    """Raised when API rate limit is exceeded.

    This exception is raised when the provider's rate limit
    is exceeded and requests should be retried later.

    Examples
    --------
    >>> raise RateLimitError("Rate limit exceeded", retry_after=300)
    """

    pass


class TemporaryServiceError(RetryableError):
    """Raised when provider service is temporarily unavailable.

    This exception indicates that the provider service is
    temporarily down or experiencing issues.

    Examples
    --------
    >>> raise TemporaryServiceError("Service temporarily unavailable")
    """

    pass
