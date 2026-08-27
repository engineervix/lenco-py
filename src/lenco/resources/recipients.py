"""Transfer recipients resource."""

from typing import Literal

from .._http import AsyncTransport, SyncTransport
from ..models import TransferRecipient
from ..models.common import Paginated
from ._base import drop_nones, one, paginated

RecipientType = Literal["mobile-money", "bank-account", "lenco-money", "lenco-merchant"]


class TransferRecipientsResource:
    """Synchronous access to ``/transfer-recipients``."""

    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        page: int = 1,
        type: RecipientType | None = None,
        country: str | None = None,
    ) -> Paginated[TransferRecipient]:
        """Retrieve all your transfer recipients.

        Args:
            page: Result page to fetch (1-indexed).
            type: Filter by recipient type.
            country: Filter by 2-letter country code, e.g. ``"zm"``.

        Returns:
            A page of transfer recipients with pagination metadata.
        """
        params = {"page": page, "type": type, "country": country}
        return paginated(
            self._t.request("GET", "/transfer-recipients", params=params),
            TransferRecipient,
        )

    def get(self, recipient_id: str) -> TransferRecipient:
        """Retrieve a specific transfer recipient by ID.

        Args:
            recipient_id: The 36-character recipient UUID.

        Returns:
            The matching transfer recipient.
        """
        return one(
            self._t.request("GET", f"/transfer-recipients/{recipient_id}"),
            TransferRecipient,
        )

    def create_bank_account(
        self, *, account_number: str, bank_id: str, country: str | None = None
    ) -> TransferRecipient:
        """Create a bank-account transfer recipient.

        Args:
            account_number: The recipient's account number.
            bank_id: The bank's Lenco ID (see ``client.banks.list()``).
            country: Optional 2-letter country code.

        Returns:
            The created recipient, including its ``id`` for future transfers.
        """
        body = drop_nones(
            {"accountNumber": account_number, "bankId": bank_id, "country": country}
        )
        return one(
            self._t.request("POST", "/transfer-recipients/bank-account", json=body),
            TransferRecipient,
        )

    def create_mobile_money(
        self, *, phone: str, operator: str, country: str | None = None
    ) -> TransferRecipient:
        """Create a mobile-money transfer recipient.

        Args:
            phone: The recipient's mobile money phone number.
            operator: One of ``"airtel"``, ``"mtn"``, ``"zamtel"``.
            country: Optional; currently only ``"zm"`` is supported.

        Returns:
            The created recipient.
        """
        body = drop_nones({"phone": phone, "operator": operator, "country": country})
        return one(
            self._t.request("POST", "/transfer-recipients/mobile-money", json=body),
            TransferRecipient,
        )

    def create_lenco_money(self, *, wallet_number: str) -> TransferRecipient:
        """Create a Lenco Money transfer recipient.

        Args:
            wallet_number: The recipient's Lenco Money wallet number.

        Returns:
            The created recipient.
        """
        return one(
            self._t.request(
                "POST",
                "/transfer-recipients/lenco-money",
                json={"walletNumber": wallet_number},
            ),
            TransferRecipient,
        )

    def create_lenco_merchant(self, *, till_number: str) -> TransferRecipient:
        """Create a Lenco merchant transfer recipient.

        Args:
            till_number: The merchant's till number.

        Returns:
            The created recipient.
        """
        return one(
            self._t.request(
                "POST",
                "/transfer-recipients/lenco-merchant",
                json={"tillNumber": till_number},
            ),
            TransferRecipient,
        )


class AsyncTransferRecipientsResource:
    """Asynchronous access to ``/transfer-recipients``."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        page: int = 1,
        type: RecipientType | None = None,
        country: str | None = None,
    ) -> Paginated[TransferRecipient]:
        """Retrieve all your transfer recipients."""
        params = {"page": page, "type": type, "country": country}
        return paginated(
            await self._t.request("GET", "/transfer-recipients", params=params),
            TransferRecipient,
        )

    async def get(self, recipient_id: str) -> TransferRecipient:
        """Retrieve a specific transfer recipient by ID."""
        return one(
            await self._t.request("GET", f"/transfer-recipients/{recipient_id}"),
            TransferRecipient,
        )

    async def create_bank_account(
        self, *, account_number: str, bank_id: str, country: str | None = None
    ) -> TransferRecipient:
        """Create a bank-account transfer recipient."""
        body = drop_nones(
            {"accountNumber": account_number, "bankId": bank_id, "country": country}
        )
        return one(
            await self._t.request(
                "POST", "/transfer-recipients/bank-account", json=body
            ),
            TransferRecipient,
        )

    async def create_mobile_money(
        self, *, phone: str, operator: str, country: str | None = None
    ) -> TransferRecipient:
        """Create a mobile-money transfer recipient."""
        body = drop_nones({"phone": phone, "operator": operator, "country": country})
        return one(
            await self._t.request(
                "POST", "/transfer-recipients/mobile-money", json=body
            ),
            TransferRecipient,
        )

    async def create_lenco_money(self, *, wallet_number: str) -> TransferRecipient:
        """Create a Lenco Money transfer recipient."""
        return one(
            await self._t.request(
                "POST",
                "/transfer-recipients/lenco-money",
                json={"walletNumber": wallet_number},
            ),
            TransferRecipient,
        )

    async def create_lenco_merchant(self, *, till_number: str) -> TransferRecipient:
        """Create a Lenco merchant transfer recipient."""
        return one(
            await self._t.request(
                "POST",
                "/transfer-recipients/lenco-merchant",
                json={"tillNumber": till_number},
            ),
            TransferRecipient,
        )
