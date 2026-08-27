"""Accounts resource tests — the tracer-bullet slice for the whole SDK."""

import pytest
import respx
from conftest import BASE_URL, TOKEN
from httpx import Response

from lenco import (
    AsyncLencoClient,
    LencoAuthError,
    LencoClient,
    LencoNotFoundError,
)

ACCOUNT = {
    "id": "b176cda5-7d97-4a3f-b4dd-ab0234e9e08c",
    "details": {
        "type": "lenco-merchant",
        "accountName": "Account Name",
        "tillNumber": "0000001",
    },
    "type": "Lenco Merchant",
    "status": "active",
    "createdAt": "2024-01-01T00:00:00.000Z",
    "currency": "ZMW",
    "availableBalance": "0.00",
    "ledgerBalance": "0.00",
}

LIST_RESPONSE = {
    "status": True,
    "message": "",
    "data": [ACCOUNT],
    "meta": {"total": 1, "pageCount": 1, "perPage": 100, "currentPage": 1},
}


class TestListAccounts:
    @respx.mock
    def test_lists_accounts_with_pagination(self) -> None:
        route = respx.get(f"{BASE_URL}/accounts").mock(
            return_value=Response(200, json=LIST_RESPONSE)
        )

        with LencoClient(token=TOKEN) as client:
            page = client.accounts.list()

        assert route.called
        assert route.calls[0].request.headers["Authorization"] == f"Bearer {TOKEN}"
        assert len(page.items) == 1
        account = page.items[0]
        assert account.id == ACCOUNT["id"]
        assert account.currency == "ZMW"
        assert account.details.account_name == "Account Name"
        assert page.meta is not None
        assert page.meta.total == 1
        assert page.meta.per_page == 100

    @respx.mock
    def test_passes_page_param(self) -> None:
        route = respx.get(f"{BASE_URL}/accounts").mock(
            return_value=Response(200, json=LIST_RESPONSE)
        )

        with LencoClient(token=TOKEN) as client:
            client.accounts.list(page=3)

        assert route.calls[0].request.url.params["page"] == "3"

    @respx.mock
    async def test_async_lists_accounts(self) -> None:
        respx.get(f"{BASE_URL}/accounts").mock(
            return_value=Response(200, json=LIST_RESPONSE)
        )

        async with AsyncLencoClient(token=TOKEN) as client:
            page = await client.accounts.list()

        assert page.items[0].id == ACCOUNT["id"]


class TestGetAccount:
    @respx.mock
    def test_gets_account_by_id(self) -> None:
        account_id = ACCOUNT["id"]
        respx.get(f"{BASE_URL}/accounts/{account_id}").mock(
            return_value=Response(
                200, json={"status": True, "message": "", "data": ACCOUNT}
            )
        )

        with LencoClient(token=TOKEN) as client:
            account = client.accounts.get(account_id)

        assert account.id == account_id

    @respx.mock
    def test_missing_account_raises_not_found(self) -> None:
        respx.get(f"{BASE_URL}/accounts/nope").mock(
            return_value=Response(
                404,
                json={"status": False, "message": "Account not found", "data": None},
            )
        )

        with LencoClient(token=TOKEN) as client:
            with pytest.raises(LencoNotFoundError, match="Account not found"):
                client.accounts.get("nope")


class TestAuthAndErrors:
    @respx.mock
    def test_invalid_token_raises_auth_error(self) -> None:
        respx.get(f"{BASE_URL}/accounts").mock(
            return_value=Response(
                401, json={"status": False, "message": "Unauthorized", "data": None}
            )
        )

        with LencoClient(token="bad") as client, pytest.raises(LencoAuthError):
            client.accounts.list()

    @respx.mock
    def test_status_false_envelope_on_200_raises(self) -> None:
        """Lenco can return HTTP 200 with {\"status\": false} — envelope wins."""
        respx.get(f"{BASE_URL}/accounts").mock(
            return_value=Response(
                200,
                json={"status": False, "message": "Something broke", "data": None},
            )
        )

        with LencoClient(token=TOKEN) as client:
            with pytest.raises(Exception, match="Something broke"):
                client.accounts.list()

    def test_empty_token_rejected(self) -> None:
        with pytest.raises(ValueError, match="token"):
            LencoClient(token="")
