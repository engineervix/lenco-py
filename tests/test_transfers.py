"""Transfers resource tests."""

import json

import respx
from conftest import BASE_URL, TOKEN
from fixtures import META, TRANSFER, envelope
from httpx import Response

from lenco import AsyncLencoClient, LencoClient

ACCOUNT_ID = "b176cda5-7d97-4a3f-b4dd-ab0234e9e08c"


class TestListAndGet:
    @respx.mock
    def test_lists_transfers(self) -> None:
        respx.get(f"{BASE_URL}/transfers").mock(
            return_value=Response(200, json=envelope([TRANSFER], meta=META))
        )

        with LencoClient(token=TOKEN) as client:
            page = client.transfers.list()

        transfer = page.items[0]
        assert transfer.id == TRANSFER["id"]
        assert transfer.status == "successful"
        assert transfer.credit_account is not None
        assert transfer.credit_account.account_number == "9130000000000"
        assert transfer.lenco_reference == "240010002"

    @respx.mock
    def test_list_filters(self) -> None:
        route = respx.get(f"{BASE_URL}/transfers").mock(
            return_value=Response(200, json=envelope([TRANSFER], meta=META))
        )

        with LencoClient(token=TOKEN) as client:
            client.transfers.list(
                status="failed", type="mobile-money", account_id=ACCOUNT_ID
            )

        params = route.calls[0].request.url.params
        assert params["status"] == "failed"
        assert params["type"] == "mobile-money"
        assert params["accountId"] == ACCOUNT_ID

    @respx.mock
    def test_get_by_id(self) -> None:
        respx.get(f"{BASE_URL}/transfers/{TRANSFER['id']}").mock(
            return_value=Response(200, json=envelope(TRANSFER))
        )

        with LencoClient(token=TOKEN) as client:
            transfer = client.transfers.get(TRANSFER["id"])

        assert transfer.amount == "20.00"

    @respx.mock
    def test_transfer_without_client_reference(self) -> None:
        """A transfer made outside the API (e.g. the banking app) can lack a reference."""
        no_reference = {**TRANSFER, "reference": None, "source": "banking-app"}
        respx.get(f"{BASE_URL}/transfers/{TRANSFER['id']}").mock(
            return_value=Response(200, json=envelope(no_reference))
        )

        with LencoClient(token=TOKEN) as client:
            transfer = client.transfers.get(TRANSFER["id"])

        assert transfer.reference is None

    @respx.mock
    def test_credit_account_exposes_id(self) -> None:
        """Docs show creditAccount.id — the recipient account's id."""
        with_id = {
            **TRANSFER,
            "creditAccount": {
                **TRANSFER["creditAccount"],
                "id": "d4f71d4a-eda4-4237-9976-5cbdc8a54cf3",
            },
        }
        respx.get(f"{BASE_URL}/transfers/{TRANSFER['id']}").mock(
            return_value=Response(200, json=envelope(with_id))
        )

        with LencoClient(token=TOKEN) as client:
            transfer = client.transfers.get(TRANSFER["id"])

        assert transfer.credit_account is not None
        assert transfer.credit_account.id == "d4f71d4a-eda4-4237-9976-5cbdc8a54cf3"

    @respx.mock
    def test_transfer_with_unrecognized_status_still_parses(self) -> None:
        """A future status value from Lenco must not crash the whole page."""
        future_status = {**TRANSFER, "status": "reversed"}
        respx.get(f"{BASE_URL}/transfers/{TRANSFER['id']}").mock(
            return_value=Response(200, json=envelope(future_status))
        )

        with LencoClient(token=TOKEN) as client:
            transfer = client.transfers.get(TRANSFER["id"])

        assert transfer.status == "reversed"

    @respx.mock
    def test_get_by_reference(self) -> None:
        route = respx.get(f"{BASE_URL}/transfers/status/ref-3").mock(
            return_value=Response(200, json=envelope(TRANSFER))
        )

        with LencoClient(token=TOKEN) as client:
            transfer = client.transfers.get_by_reference("ref-3")

        assert route.called
        assert transfer.reference == "ref-3"


class TestInitiate:
    @respx.mock
    def test_transfer_to_bank_account_with_inline_details(self) -> None:
        route = respx.post(f"{BASE_URL}/transfers/bank-account").mock(
            return_value=Response(200, json=envelope(TRANSFER))
        )

        with LencoClient(token=TOKEN) as client:
            transfer = client.transfers.to_bank_account(
                account_id=ACCOUNT_ID,
                amount=20.00,
                reference="ref-3",
                account_number="9130000000000",
                bank_id="002",
            )

        sent = json.loads(route.calls[0].request.content)
        assert sent["accountId"] == ACCOUNT_ID
        assert sent["amount"] == 20.00
        assert sent["reference"] == "ref-3"
        assert sent["accountNumber"] == "9130000000000"
        assert sent["bankId"] == "002"
        # Optional fields omitted entirely, not sent as null
        assert "narration" not in sent
        assert "transferRecipientId" not in sent
        assert transfer.status == "successful"

    @respx.mock
    def test_transfer_to_mobile_money(self) -> None:
        momo_transfer = {
            **TRANSFER,
            "creditAccount": {
                "type": "mobile-money",
                "accountName": "Beata Jean",
                "phone": "0750000000",
                "operator": "zamtel",
            },
        }
        route = respx.post(f"{BASE_URL}/transfers/mobile-money").mock(
            return_value=Response(200, json=envelope(momo_transfer))
        )

        with LencoClient(token=TOKEN) as client:
            transfer = client.transfers.to_mobile_money(
                account_id=ACCOUNT_ID,
                amount=20.00,
                reference="ref-4",
                phone="0750000000",
                operator="zamtel",
                country="zm",
            )

        sent = json.loads(route.calls[0].request.content)
        assert sent["phone"] == "0750000000"
        assert sent["operator"] == "zamtel"
        assert sent["country"] == "zm"
        assert transfer.credit_account is not None
        assert transfer.credit_account.phone == "0750000000"

    @respx.mock
    def test_transfer_with_saved_recipient(self) -> None:
        route = respx.post(f"{BASE_URL}/transfers/bank-account").mock(
            return_value=Response(200, json=envelope(TRANSFER))
        )

        with LencoClient(token=TOKEN) as client:
            client.transfers.to_bank_account(
                account_id=ACCOUNT_ID,
                amount=20.00,
                reference="ref-5",
                transfer_recipient_id="d4f71d4a-eda4-4237-9976-5cbdc8a54cf3",
            )

        sent = json.loads(route.calls[0].request.content)
        assert sent["transferRecipientId"] == "d4f71d4a-eda4-4237-9976-5cbdc8a54cf3"
        assert "accountNumber" not in sent

    @respx.mock
    def test_transfer_to_lenco_money(self) -> None:
        route = respx.post(f"{BASE_URL}/transfers/lenco-money").mock(
            return_value=Response(200, json=envelope(TRANSFER))
        )

        with LencoClient(token=TOKEN) as client:
            client.transfers.to_lenco_money(
                account_id=ACCOUNT_ID,
                amount=5.0,
                reference="ref-6",
                wallet_number="0000001",
            )

        sent = json.loads(route.calls[0].request.content)
        assert sent["walletNumber"] == "0000001"

    @respx.mock
    def test_transfer_to_lenco_merchant(self) -> None:
        route = respx.post(f"{BASE_URL}/transfers/lenco-merchant").mock(
            return_value=Response(200, json=envelope(TRANSFER))
        )

        with LencoClient(token=TOKEN) as client:
            client.transfers.to_lenco_merchant(
                account_id=ACCOUNT_ID,
                amount=5.0,
                reference="ref-7",
                till_number="0000001",
            )

        sent = json.loads(route.calls[0].request.content)
        assert sent["tillNumber"] == "0000001"

    @respx.mock
    def test_transfer_between_own_accounts(self) -> None:
        route = respx.post(f"{BASE_URL}/transfers/account").mock(
            return_value=Response(200, json=envelope(TRANSFER))
        )

        with LencoClient(token=TOKEN) as client:
            client.transfers.to_account(
                account_id=ACCOUNT_ID,
                credit_account_id="68f11209-451f-4a15-bfcd-d916eb8b09f4",
                amount=100.0,
                reference="ref-8",
            )

        sent = json.loads(route.calls[0].request.content)
        assert sent["creditAccountId"] == "68f11209-451f-4a15-bfcd-d916eb8b09f4"

    @respx.mock
    def test_failed_transfer_still_parses(self) -> None:
        """Transfers return HTTP 200 even when they fail — check status."""
        failed = {
            **TRANSFER,
            "status": "failed",
            "reasonForFailure": "Insufficient funds",
        }
        respx.post(f"{BASE_URL}/transfers/bank-account").mock(
            return_value=Response(200, json=envelope(failed))
        )

        with LencoClient(token=TOKEN) as client:
            transfer = client.transfers.to_bank_account(
                account_id=ACCOUNT_ID,
                amount=20.00,
                reference="ref-9",
                account_number="9130000000000",
                bank_id="002",
            )

        assert transfer.status == "failed"
        assert transfer.reason_for_failure == "Insufficient funds"

    @respx.mock
    def test_failed_transfer_with_null_currency_still_parses(self) -> None:
        """Lenco omits currency (null) on at least some failed transfers."""
        failed = {
            **TRANSFER,
            "currency": None,
            "status": "failed",
            "reasonForFailure": "You can not send less than k5",
        }
        respx.post(f"{BASE_URL}/transfers/mobile-money").mock(
            return_value=Response(200, json=envelope(failed))
        )

        with LencoClient(token=TOKEN) as client:
            transfer = client.transfers.to_mobile_money(
                account_id=ACCOUNT_ID,
                amount=3.00,
                reference="ref-10",
                phone="0966722365",
                operator="mtn",
                country="zm",
            )

        assert transfer.status == "failed"
        assert transfer.currency is None

    @respx.mock
    async def test_async_transfer_to_bank_account(self) -> None:
        respx.post(f"{BASE_URL}/transfers/bank-account").mock(
            return_value=Response(200, json=envelope(TRANSFER))
        )

        async with AsyncLencoClient(token=TOKEN) as client:
            transfer = await client.transfers.to_bank_account(
                account_id=ACCOUNT_ID,
                amount=20.00,
                reference="ref-10",
                account_number="9130000000000",
                bank_id="002",
            )

        assert transfer.status == "successful"
