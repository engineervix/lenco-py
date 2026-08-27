"""Zambian phone number normalization tests."""

import sys

import pytest

from lenco.exceptions import LencoError
from lenco.phone import normalize_zambian_phone


class TestNormalizeZambianPhone:
    def test_international_format_normalizes_to_local_shape(self) -> None:
        assert normalize_zambian_phone("+260966123456") == "0966123456"

    def test_various_input_shapes_normalize_to_the_same_local_shape(self) -> None:
        expected = "0966123456"
        assert normalize_zambian_phone("0966123456") == expected
        assert normalize_zambian_phone("260966123456") == expected
        assert normalize_zambian_phone("0966 123 456") == expected
        assert normalize_zambian_phone("+260 966 123 456") == expected

    @pytest.mark.parametrize(
        "number",
        [
            "0966123456",  # MTN
            "0760123456",  # MTN
            "0977123456",  # Airtel
            "0770123456",  # Airtel
            "0955123456",  # Zamtel
            "0750123456",  # Zamtel
        ],
    )
    def test_recognizes_mobile_numbers_from_all_three_carriers(
        self, number: str
    ) -> None:
        assert normalize_zambian_phone(number) == number

    def test_rejects_landline_numbers(self) -> None:
        with pytest.raises(ValueError):
            normalize_zambian_phone("0211234567")

    @pytest.mark.parametrize(
        "number",
        [
            "096612345",  # too short
            "09661234567",  # too long
            "+14155552671",  # non-Zambian country code
        ],
    )
    def test_rejects_invalid_numbers(self, number: str) -> None:
        with pytest.raises(ValueError):
            normalize_zambian_phone(number)

    @pytest.mark.parametrize("garbage", ["not a phone", ""])
    def test_rejects_unparseable_input(self, garbage: str) -> None:
        with pytest.raises(ValueError):
            normalize_zambian_phone(garbage)


class TestMissingPhoneExtra:
    def test_raises_lenco_error_when_phonenumbers_not_installed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setitem(sys.modules, "phonenumbers", None)

        with pytest.raises(LencoError, match=r"pip install lenco-py\[phone\]"):
            normalize_zambian_phone("0966123456")
