"""Transfer recipients resource tests."""

import json

import pydantic
import pytest
import respx
from conftest import BASE_URL, TOKEN
from fixtures import META, RECIPIENT_BANK_ACCOUNT, RECIPIENT_MOBILE_MONEY, envelope
from httpx import Response

from lenco import AsyncLencoClient, LencoClient


class TestListRecipients:
    @respx.mock
    def test_lists_recipients(self) -> None:
        respx.get(f"{BASE_URL}/transfer-recipients").mock(
            return_value=Response(
                200, json=envelope([RECIPIENT_MOBILE_MONEY], meta=META)
            )
        )

        with LencoClient(token=TOKEN) as client:
            page = client.transfer_recipients.list()

        assert len(page.items) == 1
        recipient = page.items[0]
        assert recipient.id == RECIPIENT_MOBILE_MONEY["id"]
        assert recipient.details.phone == "0750000000"
        assert page.meta is not None and page.meta.total == 1

    @respx.mock
    def test_filters(self) -> None:
        route = respx.get(f"{BASE_URL}/transfer-recipients").mock(
            return_value=Response(
                200, json=envelope([RECIPIENT_MOBILE_MONEY], meta=META)
            )
        )

        with LencoClient(token=TOKEN) as client:
            client.transfer_recipients.list(type="mobile-money", country="zm")

        params = route.calls[0].request.url.params
        assert params["type"] == "mobile-money"
        assert params["country"] == "zm"

    @respx.mock
    def test_gets_recipient_by_id(self) -> None:
        rid = RECIPIENT_BANK_ACCOUNT["id"]
        respx.get(f"{BASE_URL}/transfer-recipients/{rid}").mock(
            return_value=Response(200, json=envelope(RECIPIENT_BANK_ACCOUNT))
        )

        with LencoClient(token=TOKEN) as client:
            recipient = client.transfer_recipients.get(rid)

        assert recipient.details.account_number == "9130000000000"
        assert recipient.details.bank.name == "Absa Bank"


class TestDetailsDiscrimination:
    @respx.mock
    def test_malformed_details_error_names_only_the_matching_variant(self) -> None:
        """The `type` field must pick one RecipientDetails variant, not be
        matched against all four — the error should name only that variant."""
        malformed = {
            "id": "x",
            "details": {"type": "mobile-money", "accountName": "Beata Jean"},
            "currency": "ZMW",
            "type": "mobile-money",
            "country": "zm",
        }
        respx.get(f"{BASE_URL}/transfer-recipients/x").mock(
            return_value=Response(200, json=envelope(malformed))
        )

        with LencoClient(token=TOKEN) as client:
            with pytest.raises(pydantic.ValidationError) as exc_info:
                client.transfer_recipients.get("x")

        errors = str(exc_info.value)
        assert "details.mobile-money.phone" in errors
        assert "details.mobile-money.operator" in errors
        assert "bank-account" not in errors
        assert "lenco-money" not in errors
        assert "lenco-merchant" not in errors


class TestCreateRecipients:
    @respx.mock
    def test_creates_bank_account_recipient(self) -> None:
        route = respx.post(f"{BASE_URL}/transfer-recipients/bank-account").mock(
            return_value=Response(200, json=envelope(RECIPIENT_BANK_ACCOUNT))
        )

        with LencoClient(token=TOKEN) as client:
            recipient = client.transfer_recipients.create_bank_account(
                account_number="9130000000000", bank_id="002"
            )

        sent = json.loads(route.calls[0].request.content)
        assert sent == {"accountNumber": "9130000000000", "bankId": "002"}
        assert recipient.type == "bank-account"

    @respx.mock
    def test_creates_mobile_money_recipient(self) -> None:
        route = respx.post(f"{BASE_URL}/transfer-recipients/mobile-money").mock(
            return_value=Response(200, json=envelope(RECIPIENT_MOBILE_MONEY))
        )

        with LencoClient(token=TOKEN) as client:
            recipient = client.transfer_recipients.create_mobile_money(
                phone="0750000000", operator="zamtel", country="zm"
            )

        sent = json.loads(route.calls[0].request.content)
        assert sent == {
            "phone": "0750000000",
            "operator": "zamtel",
            "country": "zm",
        }
        assert recipient.details.operator == "zamtel"

    @respx.mock
    def test_creates_lenco_money_recipient(self) -> None:
        respx.post(f"{BASE_URL}/transfer-recipients/lenco-money").mock(
            return_value=Response(
                200,
                json=envelope(
                    {
                        "id": "abc",
                        "details": {
                            "type": "lenco-money",
                            "accountName": "Beata Jean",
                            "walletNumber": "0000001",
                        },
                        "currency": "ZMW",
                        "type": "lenco-money",
                        "country": "zm",
                    }
                ),
            )
        )

        with LencoClient(token=TOKEN) as client:
            recipient = client.transfer_recipients.create_lenco_money(
                wallet_number="0000001"
            )

        assert recipient.details.wallet_number == "0000001"

    @respx.mock
    def test_creates_lenco_merchant_recipient(self) -> None:
        respx.post(f"{BASE_URL}/transfer-recipients/lenco-merchant").mock(
            return_value=Response(
                200,
                json=envelope(
                    {
                        "id": "def",
                        "details": {
                            "type": "lenco-merchant",
                            "accountName": "Account Name",
                            "tillNumber": "0000001",
                        },
                        "currency": "ZMW",
                        "type": "lenco-merchant",
                        "country": "zm",
                    }
                ),
            )
        )

        with LencoClient(token=TOKEN) as client:
            recipient = client.transfer_recipients.create_lenco_merchant(
                till_number="0000001"
            )

        assert recipient.details.till_number == "0000001"

    @respx.mock
    async def test_async_creates_recipient(self) -> None:
        respx.post(f"{BASE_URL}/transfer-recipients/mobile-money").mock(
            return_value=Response(200, json=envelope(RECIPIENT_MOBILE_MONEY))
        )

        async with AsyncLencoClient(token=TOKEN) as client:
            recipient = await client.transfer_recipients.create_mobile_money(
                phone="0750000000", operator="zamtel"
            )

        assert recipient.id == RECIPIENT_MOBILE_MONEY["id"]
