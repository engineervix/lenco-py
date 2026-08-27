"""Collections resource tests."""

import json

import respx
from conftest import BASE_URL, TOKEN
from fixtures import COLLECTION, META, envelope
from httpx import Response

from lenco import AsyncLencoClient, LencoClient


class TestListAndGet:
    @respx.mock
    def test_lists_collections(self) -> None:
        respx.get(f"{BASE_URL}/collections").mock(
            return_value=Response(200, json=envelope([COLLECTION], meta=META))
        )

        with LencoClient(token=TOKEN) as client:
            page = client.collections.list(status="successful", country="zm")

        collection = page.items[0]
        assert collection.status == "successful"
        assert collection.mobile_money_details is not None
        assert collection.mobile_money_details.operator == "airtel"
        assert collection.settlement is not None
        assert collection.settlement.amount_settled == "9.75"
        assert collection.card_details is None

    @respx.mock
    def test_collection_without_client_reference(self) -> None:
        """A collection made outside the API (e.g. the banking app) can lack a reference."""
        no_reference = {**COLLECTION, "reference": None, "source": "banking-app"}
        respx.get(f"{BASE_URL}/collections/{COLLECTION['id']}").mock(
            return_value=Response(200, json=envelope(no_reference))
        )

        with LencoClient(token=TOKEN) as client:
            collection = client.collections.get(COLLECTION["id"])

        assert collection.reference is None

    @respx.mock
    def test_collection_with_unrecognized_status_still_parses(self) -> None:
        """Lenco's docs have already disagreed on the status enum once
        (otp-required vs. 3ds-auth-required) — a future value must not
        crash parsing of the whole page."""
        future_status = {**COLLECTION, "status": "chargeback-pending"}
        respx.get(f"{BASE_URL}/collections/{COLLECTION['id']}").mock(
            return_value=Response(200, json=envelope(future_status))
        )

        with LencoClient(token=TOKEN) as client:
            collection = client.collections.get(COLLECTION["id"])

        assert collection.status == "chargeback-pending"

    @respx.mock
    def test_collection_with_null_type(self) -> None:
        """Docs mark collection type nullable."""
        untyped = {**COLLECTION, "type": None}
        respx.get(f"{BASE_URL}/collections/{COLLECTION['id']}").mock(
            return_value=Response(200, json=envelope(untyped))
        )

        with LencoClient(token=TOKEN) as client:
            collection = client.collections.get(COLLECTION["id"])

        assert collection.type is None

    @respx.mock
    def test_get_by_reference_verifies_payment(self) -> None:
        respx.get(f"{BASE_URL}/collections/status/ref-1").mock(
            return_value=Response(200, json=envelope(COLLECTION))
        )

        with LencoClient(token=TOKEN) as client:
            collection = client.collections.get_by_reference("ref-1")

        assert collection.reference == "ref-1"
        assert collection.status == "successful"


class TestInitiate:
    @respx.mock
    def test_mobile_money_collection_starts_pay_offline(self) -> None:
        pay_offline = {
            **COLLECTION,
            "completedAt": None,
            "fee": None,
            "status": "pay-offline",
            "settlementStatus": None,
            "settlement": None,
        }
        route = respx.post(f"{BASE_URL}/collections/mobile-money").mock(
            return_value=Response(200, json=envelope(pay_offline))
        )

        with LencoClient(token=TOKEN) as client:
            collection = client.collections.from_mobile_money(
                amount=13.00,
                reference="ref-1",
                phone="0977433571",
                operator="airtel",
                country="zm",
                bearer="merchant",
            )

        sent = json.loads(route.calls[0].request.content)
        assert sent == {
            "amount": 13.00,
            "reference": "ref-1",
            "phone": "0977433571",
            "operator": "airtel",
            "country": "zm",
            "bearer": "merchant",
        }
        assert collection.status == "pay-offline"

    @respx.mock
    def test_card_collection_returns_3ds_redirect(self) -> None:
        card_collection = {
            **COLLECTION,
            "completedAt": None,
            "fee": None,
            "status": "3ds-auth-required",
            "settlementStatus": None,
            "settlement": None,
            "mobileMoneyDetails": None,
            "cardDetails": {
                "firstName": "Haim",
                "lastName": "Hasegawa",
                "bin": "555555",
                "last4": "4444",
                "cardType": "Mastercard",
            },
        }
        body = envelope(card_collection)
        body["meta"] = {
            "authorization": {
                "mode": "redirect",
                "redirect": "https://pay.lenco.co/auth/03bab921-ba51-4b44-b3da-620928e99c5a",
            }
        }
        route = respx.post(f"{BASE_URL}/collections/card").mock(
            return_value=Response(200, json=body)
        )

        with LencoClient(token=TOKEN) as client:
            result = client.collections.from_card(encrypted_payload="jwe-token")

        sent = json.loads(route.calls[0].request.content)
        assert sent == {"encryptedPayload": "jwe-token"}
        assert result.collection.status == "3ds-auth-required"
        assert result.collection.card_details is not None
        assert result.collection.card_details.last4 == "4444"
        assert result.authorization is not None
        assert result.authorization.redirect.startswith("https://pay.lenco.co/auth/")

    @respx.mock
    def test_card_collection_with_null_card_details(self) -> None:
        """Docs mark every cardDetails field nullable."""
        card_collection = {
            **COLLECTION,
            "completedAt": None,
            "fee": None,
            "settlementStatus": None,
            "settlement": None,
            "mobileMoneyDetails": None,
            "cardDetails": {
                "firstName": None,
                "lastName": None,
                "bin": None,
                "last4": None,
                "cardType": None,
            },
        }
        respx.get(f"{BASE_URL}/collections/{COLLECTION['id']}").mock(
            return_value=Response(200, json=envelope(card_collection))
        )

        with LencoClient(token=TOKEN) as client:
            collection = client.collections.get(COLLECTION["id"])

        assert collection.card_details is not None
        assert collection.card_details.last4 is None

    @respx.mock
    async def test_async_mobile_money_collection(self) -> None:
        respx.post(f"{BASE_URL}/collections/mobile-money").mock(
            return_value=Response(200, json=envelope(COLLECTION))
        )

        async with AsyncLencoClient(token=TOKEN) as client:
            collection = await client.collections.from_mobile_money(
                amount=13.00,
                reference="ref-1",
                phone="0977433571",
                operator="airtel",
            )

        assert collection.status == "successful"
