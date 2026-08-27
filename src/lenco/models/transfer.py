"""Transfer models."""

from datetime import datetime
from typing import Any, Literal

from .bank import Bank
from .common import LencoModel

# Open union: a future status value from Lenco parses as plain str instead
# of crashing the whole page — see CollectionStatus for the precedent.
TransferStatus = Literal["pending", "successful", "failed"] | str


class CreditAccount(LencoModel):
    """The account a transfer was credited to.

    Exactly one set of identifying fields is populated depending on
    ``type``: bank account (``account_number`` + ``bank``), mobile money
    (``phone`` + ``operator``), Lenco Money (``wallet_number``), or Lenco
    merchant (``till_number``).
    """

    id: str | None = None
    type: str
    account_name: str
    account_number: str | None = None
    bank: Bank | None = None
    phone: str | None = None
    operator: str | None = None
    wallet_number: str | None = None
    till_number: str | None = None


class Transfer(LencoModel):
    """A transfer initiated from one of your accounts."""

    id: str
    amount: str
    fee: str | None = None
    # Null on at least some failed transfers (observed: amount below Lenco's
    # per-operator minimum), not just when the field is genuinely unknown.
    currency: str | None = None
    narration: str | None = None
    initiated_at: datetime
    completed_at: datetime | None = None
    account_id: str
    credit_account: CreditAccount | None = None
    status: TransferStatus
    reason_for_failure: str | None = None
    reference: str | None = None
    lenco_reference: str
    extra_data: dict[str, Any] | None = None
    source: str | None = None
