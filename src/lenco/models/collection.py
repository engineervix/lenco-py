"""Collection and settlement models."""

from datetime import datetime
from typing import Literal

from .bank import Bank
from .common import LencoModel

# Open union: Lenco's own docs pages have already disagreed on this enum
# once (otp-required vs. 3ds-auth-required). Known values still type-check;
# an unrecognized future value parses as plain str instead of crashing.
CollectionStatus = (
    Literal[
        "pending",
        "successful",
        "failed",
        "pay-offline",
        "3ds-auth-required",
        "otp-required",
    ]
    | str
)


class Settlement(LencoModel):
    """A settlement crediting your account for a collection."""

    id: str
    amount_settled: str
    currency: str
    created_at: datetime
    settled_at: datetime | None = None
    status: str
    type: str
    account_id: str


class MobileMoneyDetails(LencoModel):
    """Mobile-money details of a collection."""

    country: str
    phone: str
    operator: str
    account_name: str | None = None
    operator_transaction_id: str | None = None


class BankAccountDetails(LencoModel):
    """Bank-account details of a collection."""

    account_name: str
    account_number: str
    bank: Bank | None = None


class CardDetails(LencoModel):
    """Masked card details of a collection. Never contains the full PAN."""

    first_name: str | None = None
    last_name: str | None = None
    bin: str | None = None
    last4: str | None = None
    card_type: str | None = None


class Collection(LencoModel):
    """A collection (incoming payment request)."""

    id: str
    initiated_at: datetime
    completed_at: datetime | None = None
    amount: str
    fee: str | None = None
    bearer: str | None = None
    currency: str
    reference: str | None = None
    lenco_reference: str
    type: str | None = None
    status: CollectionStatus
    source: str | None = None
    reason_for_failure: str | None = None
    settlement_status: str | None = None
    settlement: Settlement | None = None
    mobile_money_details: MobileMoneyDetails | None = None
    bank_account_details: BankAccountDetails | None = None
    card_details: CardDetails | None = None


class CardCollectionCustomer(LencoModel):
    """The paying customer's name, for a card collection payload."""

    first_name: str
    last_name: str


class CardCollectionBilling(LencoModel):
    """The paying customer's billing address, for a card collection payload."""

    street_address: str
    city: str
    postal_code: str
    country: str
    state: str | None = None


class CardCollectionCard(LencoModel):
    """The card being charged, for a card collection payload."""

    number: str
    expiry_month: str
    expiry_year: str
    cvv: str


class CardCollectionPayload(LencoModel):
    """The plaintext ``POST /collections/card`` request body.

    Encrypt with :func:`lenco.encryption.encrypt_payload` before sending —
    Lenco requires the request as a JWE, never as plaintext JSON.
    """

    email: str
    reference: str
    amount: float
    currency: str
    customer: CardCollectionCustomer
    billing: CardCollectionBilling
    card: CardCollectionCard
    bearer: str | None = None
    redirect_url: str | None = None


class CardAuthorization(LencoModel):
    """Returned in ``meta.authorization`` when a card collection needs 3DS."""

    mode: str
    redirect: str | None = None


class CardCollectionResult:
    """A card collection plus its (optional) 3DS authorization redirect."""

    def __init__(
        self, collection: Collection, authorization: CardAuthorization | None
    ) -> None:
        self.collection = collection
        self.authorization = authorization

    def __repr__(self) -> str:
        return (
            f"CardCollectionResult(collection={self.collection!r}, "
            f"authorization={self.authorization!r})"
        )
