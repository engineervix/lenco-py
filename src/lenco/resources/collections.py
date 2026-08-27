"""Collections resource: incoming payment requests.

Note:
    Like transfers, collection initiation always returns HTTP 200 — check
    the returned ``Collection.status``. Mobile-money collections start as
    ``"pay-offline"`` until the customer authorizes on their phone; card
    collections may return ``"3ds-auth-required"`` with a redirect URL.
"""

from typing import Literal

from .._http import AsyncTransport, Envelope, SyncTransport
from ..models import CardAuthorization, CardCollectionResult, Collection
from ..models.common import Paginated
from ._base import drop_nones, one, paginated

CollectionStatusFilter = Literal["pending", "successful", "failed", "pay-offline"]
CollectionType = Literal["card", "mobile-money", "bank-account"]


def _card_result(envelope: Envelope) -> CardCollectionResult:
    collection = Collection.model_validate(envelope.data)
    authorization = None
    if envelope.meta and envelope.meta.get("authorization"):
        authorization = CardAuthorization.model_validate(envelope.meta["authorization"])
    return CardCollectionResult(collection, authorization)


class CollectionsResource:
    """Synchronous access to ``/collections``."""

    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        page: int = 1,
        from_date: str | None = None,
        to_date: str | None = None,
        status: CollectionStatusFilter | None = None,
        type: CollectionType | None = None,
        country: str | None = None,
    ) -> Paginated[Collection]:
        """Retrieve your collection requests.

        Args:
            page: Result page to fetch (1-indexed).
            from_date: Start date filter, ``YYYY-MM-DD``.
            to_date: End date filter, ``YYYY-MM-DD``.
            status: Filter by status.
            type: Filter by collection channel.
            country: Filter by 2-letter country code, e.g. ``"zm"``.

        Returns:
            A page of collections with pagination metadata.
        """
        params = {
            "page": page,
            "from": from_date,
            "to": to_date,
            "status": status,
            "type": type,
            "country": country,
        }
        return paginated(
            self._t.request("GET", "/collections", params=params), Collection
        )

    def get(self, collection_id: str) -> Collection:
        """Retrieve a specific collection by its UUID."""
        return one(self._t.request("GET", f"/collections/{collection_id}"), Collection)

    def get_by_reference(self, reference: str) -> Collection:
        """Retrieve a collection by the client reference used at initiation.

        This is also the verification endpoint for popup-widget payments:
        call it from your server with the reference after ``onSuccess``.
        """
        return one(
            self._t.request("GET", f"/collections/status/{reference}"), Collection
        )

    def from_mobile_money(
        self,
        *,
        amount: float,
        reference: str,
        phone: str,
        operator: str,
        country: str | None = None,
        bearer: Literal["merchant", "customer"] | None = None,
    ) -> Collection:
        """Request a payment from a customer's mobile money phone.

        The customer must authorize the payment on their phone; the
        collection starts with status ``"pay-offline"``. Listen for the
        ``collection.successful`` webhook or poll :meth:`get_by_reference`.

        Args:
            amount: Amount to collect (decimal, e.g. ``10.75``).
            reference: Unique client reference.
            phone: The customer's mobile money phone number.
            operator: ``"airtel"``, ``"mtn"``, ``"zamtel"`` (Zambia) or
                ``"airtel"``, ``"tnm"`` (Malawi).
            country: ``"zm"`` (Zambia) or ``"mw"`` (Malawi).
            bearer: Who pays the fee — ``"merchant"`` (Lenco's documented
                default) or ``"customer"``. Pass it explicitly if it
                matters: live testing saw ``"customer"`` come back when
                omitted, on an account with no dashboard override we're
                aware of — the documented default may not always hold.

        Returns:
            The initiated collection. Inspect ``status`` for the outcome.
        """
        body = drop_nones(
            {
                "amount": amount,
                "reference": reference,
                "phone": phone,
                "operator": operator,
                "country": country,
                "bearer": bearer,
            }
        )
        return one(
            self._t.request("POST", "/collections/mobile-money", json=body),
            Collection,
        )

    def from_card(self, *, encrypted_payload: str) -> CardCollectionResult:
        """Request a payment by charging a customer's card.

        The payload must be JWE-encrypted — use
        :func:`lenco.encryption.encrypt_payload` to build it. Requires PCI
        DSS compliance on your side.

        Args:
            encrypted_payload: JWE compact-serialized card collection payload.

        Returns:
            The collection plus 3DS authorization details when the status
            is ``"3ds-auth-required"`` (redirect the customer to
            ``result.authorization.redirect``).
        """
        envelope = self._t.request(
            "POST", "/collections/card", json={"encryptedPayload": encrypted_payload}
        )
        return _card_result(envelope)


class AsyncCollectionsResource:
    """Asynchronous access to ``/collections``."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        page: int = 1,
        from_date: str | None = None,
        to_date: str | None = None,
        status: CollectionStatusFilter | None = None,
        type: CollectionType | None = None,
        country: str | None = None,
    ) -> Paginated[Collection]:
        """Retrieve your collection requests."""
        params = {
            "page": page,
            "from": from_date,
            "to": to_date,
            "status": status,
            "type": type,
            "country": country,
        }
        return paginated(
            await self._t.request("GET", "/collections", params=params), Collection
        )

    async def get(self, collection_id: str) -> Collection:
        """Retrieve a specific collection by its UUID."""
        return one(
            await self._t.request("GET", f"/collections/{collection_id}"), Collection
        )

    async def get_by_reference(self, reference: str) -> Collection:
        """Retrieve a collection by the client reference used at initiation."""
        return one(
            await self._t.request("GET", f"/collections/status/{reference}"),
            Collection,
        )

    async def from_mobile_money(
        self,
        *,
        amount: float,
        reference: str,
        phone: str,
        operator: str,
        country: str | None = None,
        bearer: Literal["merchant", "customer"] | None = None,
    ) -> Collection:
        """Request a payment from a customer's mobile money phone."""
        body = drop_nones(
            {
                "amount": amount,
                "reference": reference,
                "phone": phone,
                "operator": operator,
                "country": country,
                "bearer": bearer,
            }
        )
        return one(
            await self._t.request("POST", "/collections/mobile-money", json=body),
            Collection,
        )

    async def from_card(self, *, encrypted_payload: str) -> CardCollectionResult:
        """Request a payment by charging a customer's card."""
        envelope = await self._t.request(
            "POST", "/collections/card", json={"encryptedPayload": encrypted_payload}
        )
        return _card_result(envelope)
