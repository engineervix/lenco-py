"""Bank model."""

from .common import LencoModel


class Bank(LencoModel):
    """A bank or financial institution supported by Lenco."""

    id: str
    name: str
    country: str
