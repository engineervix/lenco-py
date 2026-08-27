"""Transport-level tests: response handling in _http.py."""

import time
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime

import httpx
import pytest
import respx
from conftest import BASE_URL, TOKEN
from httpx import Response

from lenco import AsyncLencoClient, LencoClient, __version__
from lenco.exceptions import (
    LencoAPIError,
    LencoDuplicateReferenceError,
    LencoServerError,
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


class TestRetry:
    @respx.mock
    def test_get_retries_after_server_error(self) -> None:
        route = respx.get(f"{BASE_URL}/banks").mock(
            side_effect=[
                Response(500, json={"status": False, "message": "boom"}),
                Response(200, json={"status": True, "data": []}),
            ]
        )

        with LencoClient(token=TOKEN) as client:
            client.banks.list()

        assert route.call_count == 2

    @respx.mock
    def test_post_is_not_retried(self) -> None:
        """POST is never auto-retried — see docs/guide/errors.md#retrying-safely.
        Lenco has no idempotency keys, so a retried POST risks a second
        transfer/collection instead of a safe re-read."""
        route = respx.post(f"{BASE_URL}/transfers/mobile-money").mock(
            return_value=Response(500, json={"status": False, "message": "boom"})
        )

        with LencoClient(token=TOKEN) as client:
            with pytest.raises(LencoServerError):
                client.transfers.to_mobile_money(
                    account_id=ACCOUNT_ID,
                    amount=20.00,
                    reference="ref-6",
                    phone="0750000000",
                    operator="zamtel",
                    country="zm",
                )

        assert route.call_count == 1

    @respx.mock
    def test_get_retries_after_connection_error(self) -> None:
        route = respx.get(f"{BASE_URL}/banks").mock(
            side_effect=[
                httpx.ConnectError("connection refused"),
                Response(200, json={"status": True, "data": []}),
            ]
        )

        with LencoClient(token=TOKEN) as client:
            client.banks.list()

        assert route.call_count == 2

    @respx.mock
    def test_exhausted_retries_raise_mapped_exception(self) -> None:
        """All attempts failing must still raise — not be silently swallowed."""
        route = respx.get(f"{BASE_URL}/banks").mock(
            return_value=Response(503, json={"status": False, "message": "down"})
        )

        with LencoClient(token=TOKEN, max_retries=2) as client:
            with pytest.raises(LencoServerError):
                client.banks.list()

        assert route.call_count == 3  # 1 initial + 2 retries

    @respx.mock
    def test_max_retries_zero_disables_retries(self) -> None:
        route = respx.get(f"{BASE_URL}/banks").mock(
            return_value=Response(500, json={"status": False, "message": "boom"})
        )

        with LencoClient(token=TOKEN, max_retries=0) as client:
            with pytest.raises(LencoServerError):
                client.banks.list()

        assert route.call_count == 1

    @respx.mock
    def test_backoff_delay_follows_full_jitter_formula(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """sleep = random_between(0, min(cap, base * 2 ** attempt)) — the
        "full jitter" formula. Assert bounds, not exact values: jitter is
        random by design (avoids synchronized retry storms across clients)."""
        sleeps: list[float] = []
        monkeypatch.setattr(time, "sleep", lambda seconds: sleeps.append(seconds))

        respx.get(f"{BASE_URL}/banks").mock(
            side_effect=[
                Response(500, json={"status": False, "message": "boom"}),
                Response(500, json={"status": False, "message": "boom"}),
                Response(200, json={"status": True, "data": []}),
            ]
        )

        with LencoClient(token=TOKEN) as client:
            client.banks.list()

        assert len(sleeps) == 2
        assert 0 <= sleeps[0] <= 1  # attempt 0: min(cap, 1 * 2**0) == 1
        assert 0 <= sleeps[1] <= 2  # attempt 1: min(cap, 1 * 2**1) == 2

    @respx.mock
    def test_retry_after_header_honored_on_429(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A 429's Retry-After overrides the exponential formula — the
        server is telling us exactly how long to wait, not guessing."""
        sleeps: list[float] = []
        monkeypatch.setattr(time, "sleep", lambda seconds: sleeps.append(seconds))

        respx.get(f"{BASE_URL}/banks").mock(
            side_effect=[
                Response(
                    429,
                    headers={"Retry-After": "5"},
                    json={"status": False, "message": "slow down"},
                ),
                Response(200, json={"status": True, "data": []}),
            ]
        )

        with LencoClient(token=TOKEN) as client:
            client.banks.list()

        assert len(sleeps) == 1
        # Small jitter added on top per state-of-practice guidance — never
        # less than what the server asked for, capped at +10%.
        assert 5 <= sleeps[0] <= 5.5

    @respx.mock
    def test_retry_after_header_accepts_http_date_format(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Retry-After is valid as either delta-seconds or an HTTP-date —
        assuming it's always seconds is a documented, common bug."""
        sleeps: list[float] = []
        monkeypatch.setattr(time, "sleep", lambda seconds: sleeps.append(seconds))

        future = format_datetime(datetime.now(UTC) + timedelta(seconds=5), usegmt=True)
        respx.get(f"{BASE_URL}/banks").mock(
            side_effect=[
                Response(
                    429,
                    headers={"Retry-After": future},
                    json={"status": False, "message": "slow down"},
                ),
                Response(200, json={"status": True, "data": []}),
            ]
        )

        with LencoClient(token=TOKEN) as client:
            client.banks.list()

        assert len(sleeps) == 1
        # Allow slack either side: wall-clock rounding on the way in, plus
        # the same up-to-10% jitter as the seconds-format case.
        assert 4 <= sleeps[0] <= 5.5

    @respx.mock
    def test_retry_after_header_is_capped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A misbehaving (or malicious) server sending an absurd Retry-After
        must not hang the client — cap it like the exponential formula."""
        sleeps: list[float] = []
        monkeypatch.setattr(time, "sleep", lambda seconds: sleeps.append(seconds))

        respx.get(f"{BASE_URL}/banks").mock(
            side_effect=[
                Response(
                    429,
                    headers={"Retry-After": "999999999"},
                    json={"status": False, "message": "slow down"},
                ),
                Response(200, json={"status": True, "data": []}),
            ]
        )

        with LencoClient(token=TOKEN) as client:
            client.banks.list()

        assert len(sleeps) == 1
        assert sleeps[0] <= 33  # cap (30s) + up to 10% jitter

    @respx.mock
    async def test_async_get_retries_after_server_error(self) -> None:
        route = respx.get(f"{BASE_URL}/banks").mock(
            side_effect=[
                Response(500, json={"status": False, "message": "boom"}),
                Response(200, json={"status": True, "data": []}),
            ]
        )

        async with AsyncLencoClient(token=TOKEN) as client:
            await client.banks.list()

        assert route.call_count == 2

    @respx.mock
    async def test_async_post_is_not_retried(self) -> None:
        route = respx.post(f"{BASE_URL}/transfers/mobile-money").mock(
            return_value=Response(500, json={"status": False, "message": "boom"})
        )

        async with AsyncLencoClient(token=TOKEN) as client:
            with pytest.raises(LencoServerError):
                await client.transfers.to_mobile_money(
                    account_id=ACCOUNT_ID,
                    amount=20.00,
                    reference="ref-7",
                    phone="0750000000",
                    operator="zamtel",
                    country="zm",
                )

        assert route.call_count == 1

    @respx.mock
    async def test_async_get_retries_after_connection_error(self) -> None:
        route = respx.get(f"{BASE_URL}/banks").mock(
            side_effect=[
                httpx.ConnectError("connection refused"),
                Response(200, json={"status": True, "data": []}),
            ]
        )

        async with AsyncLencoClient(token=TOKEN) as client:
            await client.banks.list()

        assert route.call_count == 2

    @respx.mock
    async def test_async_max_retries_zero_disables_retries(self) -> None:
        route = respx.get(f"{BASE_URL}/banks").mock(
            return_value=Response(500, json={"status": False, "message": "boom"})
        )

        async with AsyncLencoClient(token=TOKEN, max_retries=0) as client:
            with pytest.raises(LencoServerError):
                await client.banks.list()

        assert route.call_count == 1

    @respx.mock
    def test_byo_http_client_bypasses_our_retry_transport(self) -> None:
        """A caller-supplied httpx.Client owns its own retry behavior —
        see the http_client docstring on LencoClient."""
        route = respx.get(f"{BASE_URL}/banks").mock(
            return_value=Response(500, json={"status": False, "message": "boom"})
        )

        byo_client = httpx.Client(base_url=BASE_URL)
        with LencoClient(token=TOKEN, http_client=byo_client) as client:
            with pytest.raises(LencoServerError):
                client.banks.list()

        assert route.call_count == 1


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
