"""Python SDK for the Lenco API v2.

Quickstart:
    >>> from lenco import LencoClient
    >>> client = LencoClient(token="your-api-token")
    >>> accounts = client.accounts.list()
"""

from .client import AsyncLencoClient, LencoClient
from .exceptions import (
    LencoAPIError,
    LencoAuthError,
    LencoConnectionError,
    LencoError,
    LencoNotFoundError,
    LencoRateLimitError,
    LencoServerError,
    LencoValidationError,
    LencoWebhookVerificationError,
)

__version__ = "0.1.0"

__all__ = [
    "AsyncLencoClient",
    "LencoClient",
    "LencoAPIError",
    "LencoAuthError",
    "LencoConnectionError",
    "LencoError",
    "LencoNotFoundError",
    "LencoRateLimitError",
    "LencoServerError",
    "LencoValidationError",
    "LencoWebhookVerificationError",
    "__version__",
]
