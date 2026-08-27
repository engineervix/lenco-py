"""Settlements and transactions resource tests."""

import respx
from conftest import BASE_URL, TOKEN
from fixtures import COLLECTION, META, SETTLEMENT, TRANSACTION, envelope
from httpx import Response

from lenco import AsyncLencoClient, LencoClient


class TestSettlements:
    @respx.mock
    def test_lists_settlements_with_collection(self) -> None:
        respx.get(f"{BASE_URL}/settlements").mock(
            return_value=Response(200, json=envelope([SETTLEMENT], meta=META))
        )

        with LencoClient(token=TOKEN) as client:
            page = client.settlements.list(status="settled", type="instant")

        settlement = page.items[0]
        assert settlement.amount_settled == "9.75"
        assert settlement.type == "instant"
        assert settlement.collection is not None
        assert settlement.collection.reference == "ref-1"

    @respx.mock
    def test_settlement_collection_with_otp_required_status(self) -> None:
        """Settlements docs list otp-required as a nested collection status."""
        otp_collection = {**COLLECTION, "status": "otp-required"}
        settlement = {**SETTLEMENT, "collection": otp_collection}
        respx.get(f"{BASE_URL}/settlements/{SETTLEMENT['id']}").mock(
            return_value=Response(200, json=envelope(settlement))
        )

        with LencoClient(token=TOKEN) as client:
            result = client.settlements.get(SETTLEMENT["id"])

        assert result.collection is not None
        assert result.collection.status == "otp-required"

    @respx.mock
    def test_get_settlement_by_id(self) -> None:
        respx.get(f"{BASE_URL}/settlements/{SETTLEMENT['id']}").mock(
            return_value=Response(200, json=envelope(SETTLEMENT))
        )

        with LencoClient(token=TOKEN) as client:
            settlement = client.settlements.get(SETTLEMENT["id"])

        assert settlement.status == "settled"

    @respx.mock
    async def test_async_lists_settlements(self) -> None:
        respx.get(f"{BASE_URL}/settlements").mock(
            return_value=Response(200, json=envelope([SETTLEMENT], meta=META))
        )

        async with AsyncLencoClient(token=TOKEN) as client:
            page = await client.settlements.list()

        assert page.items[0].id == SETTLEMENT["id"]


class TestTransactions:
    @respx.mock
    def test_lists_transactions(self) -> None:
        route = respx.get(f"{BASE_URL}/transactions").mock(
            return_value=Response(200, json=envelope([TRANSACTION], meta=META))
        )

        with LencoClient(token=TOKEN) as client:
            page = client.transactions.list(
                type="debit", account_id=TRANSACTION["accountId"]
            )

        params = route.calls[0].request.url.params
        assert params["type"] == "debit"
        assert params["accountId"] == TRANSACTION["accountId"]
        txn = page.items[0]
        assert txn.type == "debit"
        assert txn.balance == "997559.00"
        assert txn.narration == "Transfer / 240730006"

    @respx.mock
    def test_get_transaction_by_id(self) -> None:
        respx.get(f"{BASE_URL}/transactions/{TRANSACTION['id']}").mock(
            return_value=Response(200, json=envelope(TRANSACTION))
        )

        with LencoClient(token=TOKEN) as client:
            txn = client.transactions.get(TRANSACTION["id"])

        assert txn.currency == "ZMW"

    @respx.mock
    async def test_async_lists_transactions(self) -> None:
        respx.get(f"{BASE_URL}/transactions").mock(
            return_value=Response(200, json=envelope([TRANSACTION], meta=META))
        )

        async with AsyncLencoClient(token=TOKEN) as client:
            page = await client.transactions.list()

        assert page.items[0].id == TRANSACTION["id"]
