"""Resolve resource: verify account details before sending money."""

from .._http import AsyncTransport, SyncTransport
from ..models import (
    ResolvedBankAccount,
    ResolvedLencoMerchantAccount,
    ResolvedLencoMoneyAccount,
    ResolvedMobileMoneyAccount,
)
from ._base import drop_nones, one


class ResolveResource:
    """Synchronous access to ``/resolve/*``."""

    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def bank_account(
        self, *, account_number: str, bank_id: str, country: str | None = None
    ) -> ResolvedBankAccount:
        """Verify a bank account number and return the account holder's name.

        Args:
            account_number: The account number to resolve.
            bank_id: The bank's Lenco ID (see ``client.banks.list()``).
            country: Optional 2-letter country code, e.g. ``"zm"``.

        Returns:
            The resolved account details.
        """
        body = drop_nones(
            {"accountNumber": account_number, "bankId": bank_id, "country": country}
        )
        return one(
            self._t.request("POST", "/resolve/bank-account", json=body),
            ResolvedBankAccount,
        )

    def mobile_money(
        self, *, phone: str, operator: str, country: str | None = None
    ) -> ResolvedMobileMoneyAccount:
        """Verify a mobile money phone number.

        Args:
            phone: The mobile money phone number.
            operator: One of ``"airtel"``, ``"mtn"``, ``"zamtel"``.
            country: Optional; currently only ``"zm"`` is supported.

        Returns:
            The resolved account details.
        """
        body = drop_nones({"phone": phone, "operator": operator, "country": country})
        return one(
            self._t.request("POST", "/resolve/mobile-money", json=body),
            ResolvedMobileMoneyAccount,
        )

    def lenco_money(self, *, wallet_number: str) -> ResolvedLencoMoneyAccount:
        """Verify a Lenco Money wallet number.

        Args:
            wallet_number: The wallet number to resolve.

        Returns:
            The resolved account details.
        """
        return one(
            self._t.request(
                "POST", "/resolve/lenco-money", json={"walletNumber": wallet_number}
            ),
            ResolvedLencoMoneyAccount,
        )

    def lenco_merchant(self, *, till_number: str) -> ResolvedLencoMerchantAccount:
        """Verify a Lenco merchant till number.

        Args:
            till_number: The till number to resolve.

        Returns:
            The resolved account details.
        """
        return one(
            self._t.request(
                "POST", "/resolve/lenco-merchant", json={"tillNumber": till_number}
            ),
            ResolvedLencoMerchantAccount,
        )


class AsyncResolveResource:
    """Asynchronous access to ``/resolve/*``."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def bank_account(
        self, *, account_number: str, bank_id: str, country: str | None = None
    ) -> ResolvedBankAccount:
        """Verify a bank account number and return the account holder's name."""
        body = drop_nones(
            {"accountNumber": account_number, "bankId": bank_id, "country": country}
        )
        return one(
            await self._t.request("POST", "/resolve/bank-account", json=body),
            ResolvedBankAccount,
        )

    async def mobile_money(
        self, *, phone: str, operator: str, country: str | None = None
    ) -> ResolvedMobileMoneyAccount:
        """Verify a mobile money phone number."""
        body = drop_nones({"phone": phone, "operator": operator, "country": country})
        return one(
            await self._t.request("POST", "/resolve/mobile-money", json=body),
            ResolvedMobileMoneyAccount,
        )

    async def lenco_money(self, *, wallet_number: str) -> ResolvedLencoMoneyAccount:
        """Verify a Lenco Money wallet number."""
        return one(
            await self._t.request(
                "POST", "/resolve/lenco-money", json={"walletNumber": wallet_number}
            ),
            ResolvedLencoMoneyAccount,
        )

    async def lenco_merchant(self, *, till_number: str) -> ResolvedLencoMerchantAccount:
        """Verify a Lenco merchant till number."""
        return one(
            await self._t.request(
                "POST", "/resolve/lenco-merchant", json={"tillNumber": till_number}
            ),
            ResolvedLencoMerchantAccount,
        )
