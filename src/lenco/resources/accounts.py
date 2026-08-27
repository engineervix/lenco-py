"""Accounts resource: list, retrieve, and check balances."""

from typing import Any

from .._http import AsyncTransport, Envelope, SyncTransport
from ..models import Account, AccountBalance, Meta, Paginated


def _page(envelope: Envelope) -> Paginated[Account]:
    items: list[Any] = envelope.data or []
    return Paginated(
        items=[Account.model_validate(a) for a in items],
        meta=Meta.model_validate(envelope.meta) if envelope.meta else None,
    )


def _account(envelope: Envelope) -> Account:
    return Account.model_validate(envelope.data)


def _balance(envelope: Envelope) -> AccountBalance:
    return AccountBalance.model_validate(envelope.data)


class AccountsResource:
    """Synchronous access to ``/accounts``."""

    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def list(self, *, page: int = 1) -> Paginated[Account]:
        """Retrieve information about your bank accounts.

        Args:
            page: Result page to fetch (1-indexed).

        Returns:
            A page of accounts with pagination metadata.
        """
        return _page(self._t.request("GET", "/accounts", params={"page": page}))

    def get(self, account_id: str) -> Account:
        """Retrieve a specific bank account by its ID.

        Args:
            account_id: The 36-character account UUID.

        Returns:
            The matching account.
        """
        return _account(self._t.request("GET", f"/accounts/{account_id}"))

    def balance(self, account_id: str) -> AccountBalance:
        """Retrieve the balance of a specific bank account.

        Args:
            account_id: The 36-character account UUID.

        Returns:
            The account's balance snapshot.
        """
        return _balance(self._t.request("GET", f"/accounts/{account_id}/balance"))


class AsyncAccountsResource:
    """Asynchronous access to ``/accounts``."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def list(self, *, page: int = 1) -> Paginated[Account]:
        """Retrieve information about your bank accounts."""
        return _page(await self._t.request("GET", "/accounts", params={"page": page}))

    async def get(self, account_id: str) -> Account:
        """Retrieve a specific bank account by its ID."""
        return _account(await self._t.request("GET", f"/accounts/{account_id}"))

    async def balance(self, account_id: str) -> AccountBalance:
        """Retrieve the balance of a specific bank account."""
        return _balance(await self._t.request("GET", f"/accounts/{account_id}/balance"))
