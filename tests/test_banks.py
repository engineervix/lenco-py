"""Banks resource tests."""

import respx
from conftest import BASE_URL, TOKEN
from fixtures import BANK, envelope
from httpx import Response

from lenco import AsyncLencoClient, LencoClient


class TestListBanks:
    @respx.mock
    def test_lists_banks(self) -> None:
        respx.get(f"{BASE_URL}/banks").mock(
            return_value=Response(200, json=envelope([BANK]))
        )

        with LencoClient(token=TOKEN) as client:
            banks = client.banks.list()

        assert len(banks) == 1
        assert banks[0].name == "Absa Bank"
        assert banks[0].country == "zm"

    @respx.mock
    def test_filters_by_country(self) -> None:
        route = respx.get(f"{BASE_URL}/banks").mock(
            return_value=Response(200, json=envelope([BANK]))
        )

        with LencoClient(token=TOKEN) as client:
            client.banks.list(country="zm")

        assert route.calls[0].request.url.params["country"] == "zm"

    @respx.mock
    async def test_async_lists_banks(self) -> None:
        respx.get(f"{BASE_URL}/banks").mock(
            return_value=Response(200, json=envelope([BANK]))
        )

        async with AsyncLencoClient(token=TOKEN) as client:
            banks = await client.banks.list()

        assert banks[0].id == "002"
