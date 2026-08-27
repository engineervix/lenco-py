"""Transactions resource: credits and debits on your accounts."""

from typing import Literal

from .._http import AsyncTransport, SyncTransport
from ..models import Transaction
from ..models.common import Paginated
from ._base import one, paginated

TransactionType = Literal["credit", "debit"]


class TransactionsResource:
    """Synchronous access to ``/transactions``."""

    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        page: int = 1,
        type: TransactionType | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        search: str | None = None,
        account_id: str | None = None,
    ) -> Paginated[Transaction]:
        """Get transactions that occurred on your accounts.

        Args:
            page: Result page to fetch (1-indexed).
            type: ``"credit"`` or ``"debit"``.
            from_date: Start date filter, ``YYYY-MM-DD``.
            to_date: End date filter, ``YYYY-MM-DD``.
            search: Free-text search term.
            account_id: Filter by account UUID.

        Returns:
            A page of transactions with pagination metadata.
        """
        params = {
            "page": page,
            "type": type,
            "from": from_date,
            "to": to_date,
            "search": search,
            "accountId": account_id,
        }
        return paginated(
            self._t.request("GET", "/transactions", params=params), Transaction
        )

    def get(self, transaction_id: str) -> Transaction:
        """Retrieve a specific transaction by its UUID."""
        return one(
            self._t.request("GET", f"/transactions/{transaction_id}"), Transaction
        )


class AsyncTransactionsResource:
    """Asynchronous access to ``/transactions``."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        page: int = 1,
        type: TransactionType | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        search: str | None = None,
        account_id: str | None = None,
    ) -> Paginated[Transaction]:
        """Get transactions that occurred on your accounts."""
        params = {
            "page": page,
            "type": type,
            "from": from_date,
            "to": to_date,
            "search": search,
            "accountId": account_id,
        }
        return paginated(
            await self._t.request("GET", "/transactions", params=params), Transaction
        )

    async def get(self, transaction_id: str) -> Transaction:
        """Retrieve a specific transaction by its UUID."""
        return one(
            await self._t.request("GET", f"/transactions/{transaction_id}"),
            Transaction,
        )
