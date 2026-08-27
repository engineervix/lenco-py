"""Transport-level tests: response handling in _http.py."""

import pytest
import respx
from conftest import BASE_URL, TOKEN
from httpx import Response

from lenco import AsyncLencoClient, LencoClient, __version__
from lenco.exceptions import (
    LencoAPIError,
    LencoDuplicateReferenceError,
    LencoValidationError,
)

ACCOUNT_ID = "b176cda5-7d97-4a3f-b4dd-ab0234e9e08c"


class TestNonJsonSuccessResponse:
    @respx.mock
    def test_non_json_200_raises_lenco_api_error(self) -> None:
        """A 200 with a non-JSON body (e.g. an intermediary's HTML page)
        must raise a catchable LencoAPIError, not a raw JSONDecodeError."""
        respx.get(f"{BASE_URL}/banks").mock(
            return_value=Response(200, text="<html>not json</html>")
        )

        with LencoClient(token=TOKEN) as client:
            with pytest.raises(LencoAPIError):
                client.banks.list()

    @respx.mock
    async def test_async_non_json_200_raises_lenco_api_error(self) -> None:
        respx.get(f"{BASE_URL}/banks").mock(
            return_value=Response(200, text="<html>not json</html>")
        )

        async with AsyncLencoClient(token=TOKEN) as client:
            with pytest.raises(LencoAPIError):
                await client.banks.list()


class TestDuplicateReferenceError:
    """A resubmitted `reference` gets its own catchable exception — see
    docs/guide/errors.md#retrying-safely. It's a 400, not the generic
    envelope failure other validation errors use, so it needs its own
    coverage distinct from TestNonJsonSuccessResponse above."""

    @respx.mock
    def test_duplicate_reference_raises_specific_error(self) -> None:
        respx.post(f"{BASE_URL}/transfers/mobile-money").mock(
            return_value=Response(
                400,
                json={"status": False, "message": "Duplicate reference", "data": None},
            )
        )

        with LencoClient(token=TOKEN) as client:
            with pytest.raises(LencoDuplicateReferenceError) as exc_info:
                client.transfers.to_mobile_money(
                    account_id=ACCOUNT_ID,
                    amount=20.00,
                    reference="ref-dup",
                    phone="0750000000",
                    operator="zamtel",
                    country="zm",
                )

        assert isinstance(exc_info.value, LencoValidationError)
        assert exc_info.value.message == "Duplicate reference"

    @respx.mock
    def test_other_400_stays_generic_validation_error(self) -> None:
        """A different 400 message must not be swept into the duplicate
        subtype — only the exact documented duplicate-reference case."""
        respx.post(f"{BASE_URL}/transfers/mobile-money").mock(
            return_value=Response(
                400,
                json={"status": False, "message": "Invalid phone number", "data": None},
            )
        )

        with LencoClient(token=TOKEN) as client:
            with pytest.raises(LencoValidationError) as exc_info:
                client.transfers.to_mobile_money(
                    account_id=ACCOUNT_ID,
                    amount=20.00,
                    reference="ref-5",
                    phone="bad",
                    operator="zamtel",
                    country="zm",
                )

        assert not isinstance(exc_info.value, LencoDuplicateReferenceError)

    @respx.mock
    async def test_async_duplicate_reference_raises_specific_error(self) -> None:
        respx.post(f"{BASE_URL}/transfers/mobile-money").mock(
            return_value=Response(
                400,
                json={"status": False, "message": "Duplicate reference", "data": None},
            )
        )

        async with AsyncLencoClient(token=TOKEN) as client:
            with pytest.raises(LencoDuplicateReferenceError):
                await client.transfers.to_mobile_money(
                    account_id=ACCOUNT_ID,
                    amount=20.00,
                    reference="ref-dup",
                    phone="0750000000",
                    operator="zamtel",
                    country="zm",
                )


class TestUserAgent:
    @respx.mock
    def test_sync_sends_user_agent(self) -> None:
        route = respx.get(f"{BASE_URL}/banks").mock(
            return_value=Response(200, json={"status": True, "data": []})
        )

        with LencoClient(token=TOKEN) as client:
            client.banks.list()

        user_agent = route.calls[0].request.headers["User-Agent"]
        assert user_agent.startswith(f"lenco-py/{__version__} ")

    @respx.mock
    async def test_async_sends_user_agent(self) -> None:
        route = respx.get(f"{BASE_URL}/banks").mock(
            return_value=Response(200, json={"status": True, "data": []})
        )

        async with AsyncLencoClient(token=TOKEN) as client:
            await client.banks.list()

        user_agent = route.calls[0].request.headers["User-Agent"]
        assert user_agent.startswith(f"lenco-py/{__version__} ")
