"""Settlements resource: collection settlements credited to your accounts."""

from typing import Literal

from .._http import AsyncTransport, SyncTransport
from ..models import Collection, Settlement
from ..models.common import Paginated
from ._base import one, paginated

SettlementStatus = Literal["pending", "settled"]
SettlementType = Literal["instant", "next-day"]
CollectionType = Literal["card", "mobile-money", "bank-account"]


class SettlementWithCollection(Settlement):
    """A settlement including the collection it settled."""

    collection: Collection | None = None


class SettlementsResource:
    """Synchronous access to ``/settlements``."""

    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        page: int = 1,
        from_date: str | None = None,
        to_date: str | None = None,
        status: SettlementStatus | None = None,
        type: SettlementType | None = None,
        collection_type: CollectionType | None = None,
        country: str | None = None,
    ) -> Paginated[SettlementWithCollection]:
        """Retrieve information about your collection settlements.

        Args:
            page: Result page to fetch (1-indexed).
            from_date: Start date filter, ``YYYY-MM-DD``.
            to_date: End date filter, ``YYYY-MM-DD``.
            status: ``"pending"`` or ``"settled"``.
            type: ``"instant"`` or ``"next-day"``.
            collection_type: The channel of the original collection.
            country: Filter by 2-letter country code, e.g. ``"zm"``.

        Returns:
            A page of settlements (each with its source collection).
        """
        params = {
            "page": page,
            "from": from_date,
            "to": to_date,
            "status": status,
            "type": type,
            "collectionType": collection_type,
            "country": country,
        }
        return paginated(
            self._t.request("GET", "/settlements", params=params),
            SettlementWithCollection,
        )

    def get(self, settlement_id: str) -> SettlementWithCollection:
        """Retrieve a specific settlement by its UUID."""
        return one(
            self._t.request("GET", f"/settlements/{settlement_id}"),
            SettlementWithCollection,
        )


class AsyncSettlementsResource:
    """Asynchronous access to ``/settlements``."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        page: int = 1,
        from_date: str | None = None,
        to_date: str | None = None,
        status: SettlementStatus | None = None,
        type: SettlementType | None = None,
        collection_type: CollectionType | None = None,
        country: str | None = None,
    ) -> Paginated[SettlementWithCollection]:
        """Retrieve information about your collection settlements."""
        params = {
            "page": page,
            "from": from_date,
            "to": to_date,
            "status": status,
            "type": type,
            "collectionType": collection_type,
            "country": country,
        }
        return paginated(
            await self._t.request("GET", "/settlements", params=params),
            SettlementWithCollection,
        )

    async def get(self, settlement_id: str) -> SettlementWithCollection:
        """Retrieve a specific settlement by its UUID."""
        return one(
            await self._t.request("GET", f"/settlements/{settlement_id}"),
            SettlementWithCollection,
        )
