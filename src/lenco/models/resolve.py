"""Resolved-account models returned by the ``/resolve/*`` endpoints."""

from typing import Literal

from .bank import Bank
from .common import LencoModel


class ResolvedBankAccount(LencoModel):
    """Result of resolving a bank account number."""

    type: Literal["bank-account"] = "bank-account"
    account_name: str
    account_number: str
    bank: Bank


class ResolvedMobileMoneyAccount(LencoModel):
    """Result of resolving a mobile money phone number."""

    type: Literal["mobile-money"] = "mobile-money"
    account_name: str
    phone: str
    operator: str
    country: str | None = None


class ResolvedLencoMoneyAccount(LencoModel):
    """Result of resolving a Lenco Money wallet number."""

    type: Literal["lenco-money"] = "lenco-money"
    account_name: str
    wallet_number: str


class ResolvedLencoMerchantAccount(LencoModel):
    """Result of resolving a Lenco merchant till number."""

    type: Literal["lenco-merchant"] = "lenco-merchant"
    account_name: str
    till_number: str
