"""AI Provider Exceptions."""


class AIProviderError(Exception):
    """Base exception for AI provider errors."""

    pass


class AIProviderTimeoutError(AIProviderError):
    """Raised when AI provider request times out."""

    pass


class AIProviderRateLimitError(AIProviderError):
    """Raised when AI provider rate limit is exceeded."""

    pass


class AIProviderAuthenticationError(AIProviderError):
    """Raised when AI provider authentication fails."""

    pass


class AIProviderValidationError(AIProviderError):
    """Raised when AI output fails validation after retries."""

    pass
