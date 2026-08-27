"""Transport-level tests: response handling in _http.py."""

import pytest
import respx
from conftest import BASE_URL, TOKEN
from httpx import Response

from lenco import AsyncLencoClient, LencoClient, __version__
from lenco.exceptions import LencoAPIError


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
