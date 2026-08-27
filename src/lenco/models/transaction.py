"""Transaction models."""

from datetime import datetime
from typing import Literal

from .common import LencoModel


class Transaction(LencoModel):
    """A credit or debit that occurred on one of your accounts."""

    id: str
    amount: str
    currency: str
    narration: str | None = None
    type: Literal["credit", "debit"]
    datetime: datetime
    account_id: str
    balance: str | None = None
