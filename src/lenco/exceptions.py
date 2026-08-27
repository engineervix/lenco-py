"""Exception hierarchy for the Lenco SDK.

Every API failure raises a subclass of :class:`LencoError`. HTTP-level
failures map to specific subclasses so callers can catch precisely.
"""


class LencoError(Exception):
    """Base class for all Lenco SDK errors."""


class LencoAPIError(LencoError):
    """The API returned an error response.

    Args:
        message: Human-readable summary from the API ``message`` key.
        status_code: HTTP status code, if a response was received.
        error_code: Lenco's optional ``errorCode`` field.
        data: The raw ``data`` payload, when present.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
        data: object = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.data = data


class LencoAuthError(LencoAPIError):
    """Authentication failed (401): missing or invalid API token."""


class LencoNotFoundError(LencoAPIError):
    """The requested resource does not exist (404)."""


class LencoValidationError(LencoAPIError):
    """The request was rejected as invalid (400/422)."""


class LencoRateLimitError(LencoAPIError):
    """Too many requests (429)."""


class LencoServerError(LencoAPIError):
    """An error on Lenco's end (5xx)."""


class LencoConnectionError(LencoError):
    """The request could not reach Lenco (network failure, timeout)."""


class LencoWebhookVerificationError(LencoError):
    """A webhook payload failed signature verification."""
