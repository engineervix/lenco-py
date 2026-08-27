"""Async-resource coverage: every async method exercised against the mocked API.

These complement the behavioural tests by proving each async mirror method
hits the right endpoint and parses its response — the sync twins carry the
deeper assertions.
"""

import respx
from conftest import BASE_URL, TOKEN
from fixtures import (
    COLLECTION,
    META,
    PUBLIC_FIXTURES,
    RECIPIENT_MOBILE_MONEY,
    SETTLEMENT,
    TRANSACTION,
    TRANSFER,
    envelope,
)
from httpx import Response

from lenco import AsyncLencoClient

ACCOUNT = PUBLIC_FIXTURES["account"]


@respx.mock
async def test_async_full_surface() -> None:
    respx.get(f"{BASE_URL}/accounts").mock(
        return_value=Response(200, json=envelope([ACCOUNT], meta=META))
    )
    respx.get(f"{BASE_URL}/accounts/x").mock(
        return_value=Response(200, json=envelope(ACCOUNT))
    )
    respx.get(f"{BASE_URL}/accounts/x/balance").mock(
        return_value=Response(
            200,
            json=envelope(
                {
                    "accountId": "x",
                    "availableBalance": "100.00",
                    "ledgerBalance": "100.00",
                    "currency": "ZMW",
                }
            ),
        )
    )
    respx.get(f"{BASE_URL}/transfer-recipients").mock(
        return_value=Response(200, json=envelope([RECIPIENT_MOBILE_MONEY], meta=META))
    )
    respx.get(f"{BASE_URL}/transfer-recipients/x").mock(
        return_value=Response(200, json=envelope(RECIPIENT_MOBILE_MONEY))
    )
    respx.post(f"{BASE_URL}/transfer-recipients/bank-account").mock(
        return_value=Response(200, json=envelope(RECIPIENT_MOBILE_MONEY))
    )
    respx.post(f"{BASE_URL}/transfer-recipients/lenco-money").mock(
        return_value=Response(200, json=envelope(RECIPIENT_MOBILE_MONEY))
    )
    respx.post(f"{BASE_URL}/transfer-recipients/lenco-merchant").mock(
        return_value=Response(200, json=envelope(RECIPIENT_MOBILE_MONEY))
    )
    respx.get(f"{BASE_URL}/transfers").mock(
        return_value=Response(200, json=envelope([TRANSFER], meta=META))
    )
    respx.get(f"{BASE_URL}/transfers/x").mock(
        return_value=Response(200, json=envelope(TRANSFER))
    )
    respx.get(f"{BASE_URL}/transfers/status/ref-1").mock(
        return_value=Response(200, json=envelope(TRANSFER))
    )
    respx.post(f"{BASE_URL}/transfers/mobile-money").mock(
        return_value=Response(200, json=envelope(TRANSFER))
    )
    respx.post(f"{BASE_URL}/transfers/lenco-money").mock(
        return_value=Response(200, json=envelope(TRANSFER))
    )
    respx.post(f"{BASE_URL}/transfers/lenco-merchant").mock(
        return_value=Response(200, json=envelope(TRANSFER))
    )
    respx.post(f"{BASE_URL}/transfers/account").mock(
        return_value=Response(200, json=envelope(TRANSFER))
    )
    respx.get(f"{BASE_URL}/collections").mock(
        return_value=Response(200, json=envelope([COLLECTION], meta=META))
    )
    respx.get(f"{BASE_URL}/collections/x").mock(
        return_value=Response(200, json=envelope(COLLECTION))
    )
    respx.get(f"{BASE_URL}/collections/status/ref-1").mock(
        return_value=Response(200, json=envelope(COLLECTION))
    )
    respx.post(f"{BASE_URL}/collections/card").mock(
        return_value=Response(200, json=envelope(COLLECTION))
    )
    respx.get(f"{BASE_URL}/settlements/x").mock(
        return_value=Response(200, json=envelope(SETTLEMENT))
    )
    respx.get(f"{BASE_URL}/transactions/x").mock(
        return_value=Response(200, json=envelope(TRANSACTION))
    )
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

    async with AsyncLencoClient(token=TOKEN) as client:
        assert (await client.accounts.get("x")).id == ACCOUNT["id"]
        assert (await client.accounts.balance("x")).available_balance == "100.00"
        assert (await client.transfer_recipients.get("x")).id == RECIPIENT_MOBILE_MONEY[
            "id"
        ]
        assert (
            await client.transfer_recipients.create_bank_account(
                account_number="9", bank_id="002"
            )
        ).id
        assert (
            await client.transfer_recipients.create_lenco_money(wallet_number="1")
        ).id
        assert (
            await client.transfer_recipients.create_lenco_merchant(till_number="1")
        ).id
        assert (await client.transfers.get("x")).id == TRANSFER["id"]
        assert (await client.transfers.get_by_reference("ref-1")).reference == "ref-3"
        assert (
            await client.transfers.to_mobile_money(
                account_id="x", amount=1.0, reference="r", phone="07", operator="mtn"
            )
        ).id
        assert (
            await client.transfers.to_lenco_money(
                account_id="x", amount=1.0, reference="r", wallet_number="1"
            )
        ).id
        assert (
            await client.transfers.to_lenco_merchant(
                account_id="x", amount=1.0, reference="r", till_number="1"
            )
        ).id
        assert (
            await client.transfers.to_account(
                account_id="x", credit_account_id="y", amount=1.0, reference="r"
            )
        ).id
        assert (await client.collections.get("x")).id == COLLECTION["id"]
        assert (await client.collections.get_by_reference("ref-1")).reference == "ref-1"
        result = await client.collections.from_card(encrypted_payload="jwe")
        assert result.collection.id == COLLECTION["id"]
        assert result.authorization is None
        assert (await client.settlements.get("x")).id == SETTLEMENT["id"]
        assert (await client.transactions.get("x")).id == TRANSACTION["id"]
        assert (
            await client.resolve.mobile_money(phone="07", operator="mtn")
        ).operator == "zamtel"
        assert (await client.resolve.lenco_money(wallet_number="1")).wallet_number
        assert (await client.resolve.lenco_merchant(till_number="1")).till_number
