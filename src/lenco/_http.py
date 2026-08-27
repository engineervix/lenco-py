"""Shared HTTP transport for the Lenco SDK.

Owns the base URL, auth header, response-envelope parsing, and error
mapping. Resource classes never touch httpx directly — this is the only
module that does (orthogonality + reversibility: swap transport here).
"""

import platform
from dataclasses import dataclass
from typing import Any

import httpx

from .exceptions import (
    LencoAPIError,
    LencoAuthError,
    LencoConnectionError,
    LencoDuplicateReferenceError,
    LencoNotFoundError,
    LencoRateLimitError,
    LencoServerError,
    LencoValidationError,
)

DEFAULT_BASE_URL = "https://api.lenco.co/access/v2"
DEFAULT_TIMEOUT = 30.0


def _headers(token: str) -> dict[str, str]:
    # Import here, not at module top: this module loads before lenco/__init__
    # finishes setting __version__, so a top-level import would be circular.
    from . import __version__

    python_version = platform.python_version()
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": f"lenco-py/{__version__} (Python {python_version})",
    }


def raise_for_response(response: httpx.Response) -> None:
    """Map a non-2xx response (or a ``status: false`` envelope) to an exception."""
    try:
        payload: dict[str, Any] = response.json()
    except ValueError:
        payload = {}

    message = payload.get("message") or response.reason_phrase or "Lenco API error"
    error_code = payload.get("errorCode")
    data = payload.get("data")

    # Lenco sometimes returns 200 with {"status": false, ...}; the envelope
    # is authoritative in that case.
    failed_envelope = (
        response.is_success
        and isinstance(payload, dict)
        and payload.get("status") is False
    )
    if response.is_success and not failed_envelope:
        return

    cls: type[LencoAPIError]
    if response.status_code == 401:
        cls = LencoAuthError
    elif response.status_code == 404:
        cls = LencoNotFoundError
    elif response.status_code == 400 and message == "Duplicate reference":
        cls = LencoDuplicateReferenceError
    elif response.status_code in (400, 422) or failed_envelope:
        cls = LencoValidationError
    elif response.status_code == 429:
        cls = LencoRateLimitError
    elif response.status_code >= 500:
        cls = LencoServerError
    else:
        cls = LencoAPIError

    raise cls(
        message, status_code=response.status_code, error_code=error_code, data=data
    )


def _parse_json_or_error(response: httpx.Response) -> dict[str, Any]:
    """Parse a successful response as JSON, or raise if the body isn't JSON."""
    try:
        payload: dict[str, Any] = response.json()
    except ValueError as exc:
        raise LencoAPIError(
            "Lenco API returned a non-JSON response",
            status_code=response.status_code,
        ) from exc
    return payload


@dataclass
class Envelope:
    """Parsed Lenco response envelope: ``{status, message, data, meta?}``."""

    status: bool
    message: str
    data: Any
    meta: dict[str, Any] | None

    @classmethod
    def parse(cls, payload: dict[str, Any]) -> "Envelope":
        return cls(
            status=bool(payload.get("status", True)),
            message=payload.get("message", ""),
            data=payload.get("data"),
            meta=payload.get("meta"),
        )


class SyncTransport:
    """Blocking transport backed by ``httpx.Client``."""

    def __init__(
        self,
        token: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        client: httpx.Client | None = None,
    ) -> None:
        self._client = client or httpx.Client(
            base_url=base_url, headers=_headers(token), timeout=timeout
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> Envelope:
        """Perform a request and return the parsed response envelope.

        Raises:
            LencoAPIError: On any API-level failure.
            LencoConnectionError: On network failure.
        """
        try:
            response = self._client.request(
                method, path, params=_clean(params), json=json
            )
        except httpx.HTTPError as exc:
            raise LencoConnectionError(str(exc)) from exc
        raise_for_response(response)
        return Envelope.parse(_parse_json_or_error(response))

    def close(self) -> None:
        self._client.close()


class AsyncTransport:
    """Non-blocking transport backed by ``httpx.AsyncClient``."""

    def __init__(
        self,
        token: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._client = client or httpx.AsyncClient(
            base_url=base_url, headers=_headers(token), timeout=timeout
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> Envelope:
        try:
            response = await self._client.request(
                method, path, params=_clean(params), json=json
            )
        except httpx.HTTPError as exc:
            raise LencoConnectionError(str(exc)) from exc
        raise_for_response(response)
        return Envelope.parse(_parse_json_or_error(response))

    async def aclose(self) -> None:
        await self._client.aclose()


def _clean(params: dict[str, Any] | None) -> dict[str, Any] | None:
    """Drop ``None`` values so optional query params are omitted, not sent as 'None'."""
    if params is None:
        return None
    return {k: v for k, v in params.items() if v is not None}
