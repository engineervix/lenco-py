"""Account models."""

from datetime import datetime

from .common import LencoModel


class AccountDetails(LencoModel):
    """Type-specific details of an account (e.g. till number for merchants)."""

    type: str
    account_name: str
    till_number: str | None = None


class Account(LencoModel):
    """A Lenco bank account."""

    id: str
    details: AccountDetails
    type: str
    status: str
    created_at: datetime
    currency: str
    available_balance: str | None = None
    ledger_balance: str | None = None


class AccountBalance(LencoModel):
    """Balance snapshot for an account."""

    available_balance: str | None = None
    ledger_balance: str | None = None
    currency: str | None = None
