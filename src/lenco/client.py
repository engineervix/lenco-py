"""Top-level Lenco API clients.

``LencoClient`` is the blocking client; ``AsyncLencoClient`` is the
non-blocking equivalent for async frameworks like FastAPI. Both expose the
same resource attributes and models.
"""

import httpx

from ._http import DEFAULT_BASE_URL, AsyncTransport, SyncTransport
from .encryption import AsyncEncryptionResource, EncryptionResource
from .resources.accounts import AccountsResource, AsyncAccountsResource
from .resources.banks import AsyncBanksResource, BanksResource
from .resources.collections import AsyncCollectionsResource, CollectionsResource
from .resources.recipients import (
    AsyncTransferRecipientsResource,
    TransferRecipientsResource,
)
from .resources.resolve import AsyncResolveResource, ResolveResource
from .resources.settlements import AsyncSettlementsResource, SettlementsResource
from .resources.transactions import AsyncTransactionsResource, TransactionsResource
from .resources.transfers import AsyncTransfersResource, TransfersResource


class LencoClient:
    """Synchronous client for the Lenco API v2.

    Args:
        token: Your Lenco API token (secret key). Required.
        base_url: API base URL; override only for testing.
        timeout: Request timeout in seconds.
        http_client: Bring-your-own ``httpx.Client`` (optional).

    Example:
        >>> with LencoClient(token="...") as client:
        ...     accounts = client.accounts.list()
    """

    def __init__(
        self,
        token: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        if not token:
            raise ValueError("A Lenco API token is required")
        transport = SyncTransport(
            token, base_url=base_url, timeout=timeout, client=http_client
        )
        self._transport = transport
        self.accounts = AccountsResource(transport)
        self.banks = BanksResource(transport)
        self.resolve = ResolveResource(transport)
        self.transfer_recipients = TransferRecipientsResource(transport)
        self.transfers = TransfersResource(transport)
        self.collections = CollectionsResource(transport)
        self.settlements = SettlementsResource(transport)
        self.transactions = TransactionsResource(transport)
        self.encryption = EncryptionResource(transport)

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._transport.close()

    def __enter__(self) -> "LencoClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncLencoClient:
    """Asynchronous client for the Lenco API v2.

    Same resources as :class:`LencoClient`, awaited:

    Example:
        >>> async with AsyncLencoClient(token="...") as client:
        ...     accounts = await client.accounts.list()
    """

    def __init__(
        self,
        token: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        if not token:
            raise ValueError("A Lenco API token is required")
        transport = AsyncTransport(
            token, base_url=base_url, timeout=timeout, client=http_client
        )
        self._transport = transport
        self.accounts = AsyncAccountsResource(transport)
        self.banks = AsyncBanksResource(transport)
        self.resolve = AsyncResolveResource(transport)
        self.transfer_recipients = AsyncTransferRecipientsResource(transport)
        self.transfers = AsyncTransfersResource(transport)
        self.collections = AsyncCollectionsResource(transport)
        self.settlements = AsyncSettlementsResource(transport)
        self.transactions = AsyncTransactionsResource(transport)
        self.encryption = AsyncEncryptionResource(transport)

    async def aclose(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._transport.aclose()

    async def __aenter__(self) -> "AsyncLencoClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()
