"""Banks resource: list supported banks and financial institutions."""

from typing import Any

from .._http import AsyncTransport, SyncTransport
from ..models import Bank


def _banks(data: Any) -> list[Bank]:
    items: list[Any] = data or []
    return [Bank.model_validate(b) for b in items]


class BanksResource:
    """Synchronous access to ``/banks``."""

    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def list(self, *, country: str | None = None) -> list[Bank]:
        """Get the list of banks and financial institutions.

        Args:
            country: Optional 2-letter country filter, e.g. ``"zm"``.

        Returns:
            The supported banks, optionally filtered by country.
        """
        envelope = self._t.request("GET", "/banks", params={"country": country})
        return _banks(envelope.data)


class AsyncBanksResource:
    """Asynchronous access to ``/banks``."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def list(self, *, country: str | None = None) -> list[Bank]:
        """Get the list of banks and financial institutions."""
        envelope = await self._t.request("GET", "/banks", params={"country": country})
        return _banks(envelope.data)
