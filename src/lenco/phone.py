"""Zambian phone number normalization.

Lenco's mobile money APIs expect Zambian phone numbers in local
``0XXXXXXXXX`` shape. This module normalizes the common input shapes
(``+260...``, ``260...``, ``0...``, with or without spaces) to that shape.

Requires the ``phone`` extra: ``pip install lenco-py[phone]``.
"""

from .exceptions import LencoError


def normalize_zambian_phone(phone: str) -> str:
    """Normalize a Zambian mobile number to local ``0XXXXXXXXX`` shape.

    Args:
        phone: A Zambian phone number in any common shape, e.g.
            ``"+260966123456"``, ``"260966123456"``, ``"0966123456"``, or
            with stray spaces.

    Returns:
        The number in local ``0XXXXXXXXX`` shape, e.g. ``"0966123456"``.
    """
    try:
        import phonenumbers
    except ImportError as exc:
        raise LencoError(
            "Phone normalization requires the 'phone' extra: "
            "pip install lenco-py[phone]"
        ) from exc

    try:
        parsed = phonenumbers.parse(phone, "ZM")
    except phonenumbers.NumberParseException as exc:
        raise ValueError(f"{phone!r} is not a valid phone number") from exc

    if phonenumbers.number_type(parsed) != phonenumbers.PhoneNumberType.MOBILE:
        raise ValueError(f"{phone!r} is not a Zambian mobile number")

    return f"0{parsed.national_number}"
