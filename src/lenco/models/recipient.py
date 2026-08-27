"""Transfer recipient models."""

from typing import Annotated, Literal

from pydantic import Field

from .bank import Bank
from .common import LencoModel


class RecipientBankAccountDetails(LencoModel):
    """Details of a bank-account recipient."""

    type: Literal["bank-account"] = "bank-account"
    account_name: str
    account_number: str
    bank: Bank | None = None


class RecipientMobileMoneyDetails(LencoModel):
    """Details of a mobile-money recipient."""

    type: Literal["mobile-money"] = "mobile-money"
    account_name: str
    phone: str
    operator: str


class RecipientLencoMoneyDetails(LencoModel):
    """Details of a Lenco Money recipient."""

    type: Literal["lenco-money"] = "lenco-money"
    account_name: str
    wallet_number: str


class RecipientLencoMerchantDetails(LencoModel):
    """Details of a Lenco merchant recipient."""

    type: Literal["lenco-merchant"] = "lenco-merchant"
    account_name: str
    till_number: str


RecipientDetails = Annotated[
    RecipientBankAccountDetails
    | RecipientMobileMoneyDetails
    | RecipientLencoMoneyDetails
    | RecipientLencoMerchantDetails,
    Field(discriminator="type"),
]


class TransferRecipient(LencoModel):
    """A saved transfer recipient."""

    id: str
    details: RecipientDetails
    currency: str
    type: str
    country: str
