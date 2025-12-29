class ProviderError(RuntimeError):
    """Base error for provider issues."""


class ProviderNotConfiguredError(ProviderError):
    """Raised when a provider is selected but not configured."""


class ProviderNotImplementedError(ProviderError):
    """Raised when a provider is selected but not implemented."""
