"""Transfers resource: list, query, and initiate outbound transfers.

Note:
    Lenco always returns HTTP 200 for transfer initiation — check the
    returned ``Transfer.status`` (``"successful"`` / ``"pending"`` /
    ``"failed"``) rather than relying on the HTTP status code.
"""

from typing import Any, Literal

from .._http import AsyncTransport, SyncTransport
from ..models import Transfer
from ..models.common import Paginated
from ._base import drop_nones, one, paginated

TransferType = Literal["mobile-money", "bank-account", "lenco-money", "lenco-merchant"]
TransferStatusFilter = Literal["pending", "successful", "failed"]


def _transfer_body(
    *,
    account_id: str,
    amount: float,
    reference: str,
    narration: str | None,
    transfer_recipient_id: str | None,
    extra: dict[str, Any],
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "accountId": account_id,
        "amount": amount,
        "reference": reference,
        "narration": narration,
        "transferRecipientId": transfer_recipient_id,
        **extra,
    }
    return drop_nones(body)


class TransfersResource:
    """Synchronous access to ``/transfers``."""

    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        page: int = 1,
        from_date: str | None = None,
        to_date: str | None = None,
        search: str | None = None,
        account_id: str | None = None,
        transfer_recipient_id: str | None = None,
        type: TransferType | None = None,
        status: TransferStatusFilter | None = None,
        country: str | None = None,
    ) -> Paginated[Transfer]:
        """Retrieve your transfers.

        Args:
            page: Result page to fetch (1-indexed).
            from_date: Start date filter, ``YYYY-MM-DD``.
            to_date: End date filter, ``YYYY-MM-DD``.
            search: Free-text search term.
            account_id: Filter by debited account UUID.
            transfer_recipient_id: Filter by recipient UUID.
            type: Filter by transfer type.
            status: Filter by status.
            country: Filter by 2-letter country code, e.g. ``"zm"``.

        Returns:
            A page of transfers with pagination metadata.
        """
        params = {
            "page": page,
            "from": from_date,
            "to": to_date,
            "search": search,
            "accountId": account_id,
            "transferRecipientId": transfer_recipient_id,
            "type": type,
            "status": status,
            "country": country,
        }
        return paginated(self._t.request("GET", "/transfers", params=params), Transfer)

    def get(self, transfer_id: str) -> Transfer:
        """Retrieve a specific transfer by its UUID."""
        return one(self._t.request("GET", f"/transfers/{transfer_id}"), Transfer)

    def get_by_reference(self, reference: str) -> Transfer:
        """Retrieve a transfer by the client reference used at initiation."""
        return one(self._t.request("GET", f"/transfers/status/{reference}"), Transfer)

    def to_bank_account(
        self,
        *,
        account_id: str,
        amount: float,
        reference: str,
        narration: str | None = None,
        transfer_recipient_id: str | None = None,
        account_number: str | None = None,
        bank_id: str | None = None,
        country: str | None = None,
    ) -> Transfer:
        """Initiate a transfer to a bank account.

        Args:
            account_id: Your 36-character account UUID to debit.
            amount: Amount to transfer (decimal, e.g. ``10.75``).
            reference: Unique client reference (``-``, ``.``, ``_`` and
                alphanumerics only).
            narration: Optional transfer narration.
            transfer_recipient_id: A saved recipient UUID. If omitted, pass
                ``account_number`` and ``bank_id`` instead.
            account_number: Recipient account number (with ``bank_id``).
            bank_id: Recipient bank's Lenco ID (with ``account_number``).
            country: Optional 2-letter country code, e.g. ``"zm"``.

        Returns:
            The initiated transfer. Inspect ``status`` for the outcome.
        """
        body = _transfer_body(
            account_id=account_id,
            amount=amount,
            reference=reference,
            narration=narration,
            transfer_recipient_id=transfer_recipient_id,
            extra={
                "accountNumber": account_number,
                "bankId": bank_id,
                "country": country,
            },
        )
        return one(
            self._t.request("POST", "/transfers/bank-account", json=body), Transfer
        )

    def to_mobile_money(
        self,
        *,
        account_id: str,
        amount: float,
        reference: str,
        narration: str | None = None,
        transfer_recipient_id: str | None = None,
        phone: str | None = None,
        operator: str | None = None,
        country: str | None = None,
    ) -> Transfer:
        """Initiate a transfer to a mobile money account (Zambia, Malawi).

        Args:
            account_id: Your 36-character account UUID to debit.
            amount: Amount to transfer.
            reference: Unique client reference.
            narration: Optional transfer narration.
            transfer_recipient_id: A saved recipient UUID. If omitted, pass
                ``phone`` and ``operator`` instead.
            phone: Recipient mobile money phone number (with ``operator``).
            operator: ``"airtel"``, ``"mtn"``, ``"zamtel"`` (Zambia) or
                ``"airtel"``, ``"tnm"`` (Malawi).
            country: ``"zm"`` (Zambia) or ``"mw"`` (Malawi).

        Returns:
            The initiated transfer. Inspect ``status`` for the outcome.
        """
        body = _transfer_body(
            account_id=account_id,
            amount=amount,
            reference=reference,
            narration=narration,
            transfer_recipient_id=transfer_recipient_id,
            extra={"phone": phone, "operator": operator, "country": country},
        )
        return one(
            self._t.request("POST", "/transfers/mobile-money", json=body), Transfer
        )

    def to_lenco_money(
        self,
        *,
        account_id: str,
        amount: float,
        reference: str,
        narration: str | None = None,
        transfer_recipient_id: str | None = None,
        wallet_number: str | None = None,
    ) -> Transfer:
        """Initiate a transfer to a Lenco Money wallet.

        Args:
            account_id: Your 36-character account UUID to debit.
            amount: Amount to transfer.
            reference: Unique client reference.
            narration: Optional transfer narration.
            transfer_recipient_id: A saved recipient UUID. If omitted, pass
                ``wallet_number`` instead.
            wallet_number: Recipient Lenco Money wallet number.

        Returns:
            The initiated transfer. Inspect ``status`` for the outcome.
        """
        body = _transfer_body(
            account_id=account_id,
            amount=amount,
            reference=reference,
            narration=narration,
            transfer_recipient_id=transfer_recipient_id,
            extra={"walletNumber": wallet_number},
        )
        return one(
            self._t.request("POST", "/transfers/lenco-money", json=body), Transfer
        )

    def to_lenco_merchant(
        self,
        *,
        account_id: str,
        amount: float,
        reference: str,
        narration: str | None = None,
        transfer_recipient_id: str | None = None,
        till_number: str | None = None,
    ) -> Transfer:
        """Initiate a transfer to a Lenco merchant till.

        Args:
            account_id: Your 36-character account UUID to debit.
            amount: Amount to transfer.
            reference: Unique client reference.
            narration: Optional transfer narration.
            transfer_recipient_id: A saved recipient UUID. If omitted, pass
                ``till_number`` instead.
            till_number: The merchant's till number.

        Returns:
            The initiated transfer. Inspect ``status`` for the outcome.
        """
        body = _transfer_body(
            account_id=account_id,
            amount=amount,
            reference=reference,
            narration=narration,
            transfer_recipient_id=transfer_recipient_id,
            extra={"tillNumber": till_number},
        )
        return one(
            self._t.request("POST", "/transfers/lenco-merchant", json=body), Transfer
        )

    def to_account(
        self,
        *,
        account_id: str,
        credit_account_id: str,
        amount: float,
        reference: str,
        narration: str | None = None,
    ) -> Transfer:
        """Initiate a transfer between two of your own accounts.

        Args:
            account_id: Your account UUID to debit.
            credit_account_id: Your account UUID to credit.
            amount: Amount to transfer.
            reference: Unique client reference.
            narration: Optional transfer narration.

        Returns:
            The initiated transfer. Inspect ``status`` for the outcome.
        """
        body = drop_nones(
            {
                "accountId": account_id,
                "creditAccountId": credit_account_id,
                "amount": amount,
                "reference": reference,
                "narration": narration,
            }
        )
        return one(self._t.request("POST", "/transfers/account", json=body), Transfer)


class AsyncTransfersResource:
    """Asynchronous access to ``/transfers``."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        page: int = 1,
        from_date: str | None = None,
        to_date: str | None = None,
        search: str | None = None,
        account_id: str | None = None,
        transfer_recipient_id: str | None = None,
        type: TransferType | None = None,
        status: TransferStatusFilter | None = None,
        country: str | None = None,
    ) -> Paginated[Transfer]:
        """Retrieve your transfers."""
        params = {
            "page": page,
            "from": from_date,
            "to": to_date,
            "search": search,
            "accountId": account_id,
            "transferRecipientId": transfer_recipient_id,
            "type": type,
            "status": status,
            "country": country,
        }
        return paginated(
            await self._t.request("GET", "/transfers", params=params), Transfer
        )

    async def get(self, transfer_id: str) -> Transfer:
        """Retrieve a specific transfer by its UUID."""
        return one(await self._t.request("GET", f"/transfers/{transfer_id}"), Transfer)

    async def get_by_reference(self, reference: str) -> Transfer:
        """Retrieve a transfer by the client reference used at initiation."""
        return one(
            await self._t.request("GET", f"/transfers/status/{reference}"), Transfer
        )

    async def to_bank_account(
        self,
        *,
        account_id: str,
        amount: float,
        reference: str,
        narration: str | None = None,
        transfer_recipient_id: str | None = None,
        account_number: str | None = None,
        bank_id: str | None = None,
        country: str | None = None,
    ) -> Transfer:
        """Initiate a transfer to a bank account."""
        body = _transfer_body(
            account_id=account_id,
            amount=amount,
            reference=reference,
            narration=narration,
            transfer_recipient_id=transfer_recipient_id,
            extra={
                "accountNumber": account_number,
                "bankId": bank_id,
                "country": country,
            },
        )
        return one(
            await self._t.request("POST", "/transfers/bank-account", json=body),
            Transfer,
        )

    async def to_mobile_money(
        self,
        *,
        account_id: str,
        amount: float,
        reference: str,
        narration: str | None = None,
        transfer_recipient_id: str | None = None,
        phone: str | None = None,
        operator: str | None = None,
        country: str | None = None,
    ) -> Transfer:
        """Initiate a transfer to a mobile money account (Zambia, Malawi)."""
        body = _transfer_body(
            account_id=account_id,
            amount=amount,
            reference=reference,
            narration=narration,
            transfer_recipient_id=transfer_recipient_id,
            extra={"phone": phone, "operator": operator, "country": country},
        )
        return one(
            await self._t.request("POST", "/transfers/mobile-money", json=body),
            Transfer,
        )

    async def to_lenco_money(
        self,
        *,
        account_id: str,
        amount: float,
        reference: str,
        narration: str | None = None,
        transfer_recipient_id: str | None = None,
        wallet_number: str | None = None,
    ) -> Transfer:
        """Initiate a transfer to a Lenco Money wallet."""
        body = _transfer_body(
            account_id=account_id,
            amount=amount,
            reference=reference,
            narration=narration,
            transfer_recipient_id=transfer_recipient_id,
            extra={"walletNumber": wallet_number},
        )
        return one(
            await self._t.request("POST", "/transfers/lenco-money", json=body),
            Transfer,
        )

    async def to_lenco_merchant(
        self,
        *,
        account_id: str,
        amount: float,
        reference: str,
        narration: str | None = None,
        transfer_recipient_id: str | None = None,
        till_number: str | None = None,
    ) -> Transfer:
        """Initiate a transfer to a Lenco merchant till."""
        body = _transfer_body(
            account_id=account_id,
            amount=amount,
            reference=reference,
            narration=narration,
            transfer_recipient_id=transfer_recipient_id,
            extra={"tillNumber": till_number},
        )
        return one(
            await self._t.request("POST", "/transfers/lenco-merchant", json=body),
            Transfer,
        )

    async def to_account(
        self,
        *,
        account_id: str,
        credit_account_id: str,
        amount: float,
        reference: str,
        narration: str | None = None,
    ) -> Transfer:
        """Initiate a transfer between two of your own accounts."""
        body = drop_nones(
            {
                "accountId": account_id,
                "creditAccountId": credit_account_id,
                "amount": amount,
                "reference": reference,
                "narration": narration,
            }
        )
        return one(
            await self._t.request("POST", "/transfers/account", json=body), Transfer
        )
