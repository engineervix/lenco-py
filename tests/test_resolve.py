"""Resolve resource tests."""

import pytest
import respx
from conftest import BASE_URL, TOKEN
from fixtures import BANK, envelope
from httpx import Response

from lenco import AsyncLencoClient, LencoClient, LencoValidationError


class TestResolveBankAccount:
    @respx.mock
    def test_resolves_bank_account(self) -> None:
        route = respx.post(f"{BASE_URL}/resolve/bank-account").mock(
            return_value=Response(
                200,
                json=envelope(
                    {
                        "type": "bank-account",
                        "accountName": "Beata Jean",
                        "accountNumber": "9130000000000",
                        "bank": BANK,
                    }
                ),
            )
        )

        with LencoClient(token=TOKEN) as client:
            resolved = client.resolve.bank_account(
                account_number="9130000000000", bank_id="002"
            )

        assert resolved.account_name == "Beata Jean"
        assert resolved.bank.name == "Absa Bank"
        import json

        sent = json.loads(route.calls[0].request.content)
        assert sent == {"accountNumber": "9130000000000", "bankId": "002"}

    @respx.mock
    def test_unknown_account_raises_validation_error(self) -> None:
        respx.post(f"{BASE_URL}/resolve/bank-account").mock(
            return_value=Response(
                400,
                json={
                    "status": False,
                    "message": "Account details was not found",
                    "data": None,
                },
            )
        )

        with (
            LencoClient(token=TOKEN) as client,
            pytest.raises(LencoValidationError, match="Account details was not found"),
        ):
            client.resolve.bank_account(account_number="0000", bank_id="002")

    @respx.mock
    async def test_async_resolves_bank_account(self) -> None:
        respx.post(f"{BASE_URL}/resolve/bank-account").mock(
            return_value=Response(
                200,
                json=envelope(
                    {
                        "type": "bank-account",
                        "accountName": "Beata Jean",
                        "accountNumber": "9130000000000",
                        "bank": BANK,
                    }
                ),
            )
        )

        async with AsyncLencoClient(token=TOKEN) as client:
            resolved = await client.resolve.bank_account(
                account_number="9130000000000", bank_id="002"
            )

        assert resolved.account_number == "9130000000000"


class TestResolveOthers:
    @respx.mock
    def test_resolves_mobile_money(self) -> None:
        respx.post(f"{BASE_URL}/resolve/mobile-money").mock(
            return_value=Response(
                200,
                json=envelope(
                    {
                        "type": "mobile-money",
                        "accountName": "Beata Jean",
                        "phone": "0750000000",
                        "operator": "zamtel",
                        "country": "zm",
                    }
                ),
            )
        )

        with LencoClient(token=TOKEN) as client:
            resolved = client.resolve.mobile_money(
                phone="0750000000", operator="zamtel"
            )

        assert resolved.operator == "zamtel"
        assert resolved.country == "zm"

    @respx.mock
    def test_resolves_lenco_money(self) -> None:
        respx.post(f"{BASE_URL}/resolve/lenco-money").mock(
            return_value=Response(
                200,
                json=envelope(
                    {
                        "type": "lenco-money",
                        "accountName": "Beata Jean",
                        "walletNumber": "0000001",
                    }
                ),
            )
        )

        with LencoClient(token=TOKEN) as client:
            resolved = client.resolve.lenco_money(wallet_number="0000001")

        assert resolved.wallet_number == "0000001"

    @respx.mock
    def test_resolves_lenco_merchant(self) -> None:
        respx.post(f"{BASE_URL}/resolve/lenco-merchant").mock(
            return_value=Response(
                200,
                json=envelope(
                    {
                        "type": "lenco-merchant",
                        "accountName": "Account Name",
                        "tillNumber": "0000001",
                    }
                ),
            )
        )

        with LencoClient(token=TOKEN) as client:
            resolved = client.resolve.lenco_merchant(till_number="0000001")

        assert resolved.till_number == "0000001"
