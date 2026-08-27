"""Live smoke test against the real Lenco API.

Not part of the unit test suite. Run it manually with a real API token:

    LENCO_API_TOKEN=... python utils/smoke.py

Also reads simple `KEY=VALUE` / `export KEY=VALUE` lines from a `.env` or
`.envrc` in the repo root, if present (checked in that order; other lines,
e.g. direnv directives like `use flake`, are ignored). Already-exported
shell variables always win over either file.

Lenco's docs don't document a separate sandbox base URL — the officially
documented mechanism is test phone numbers/cards against the normal API (see
https://lenco-api.readme.io/v2.0/reference/test-cards-and-accounts). Set
LENCO_API_URL if you have reason to believe a distinct host applies to your
account. The msisdn/operator defaults below (0971111111 / airtel) are
Lenco's own documented "successful collection" test number for Airtel Zambia.

Optional environment variables:
    LENCO_API_URL           — override the API base URL (default: the SDK's
                              production URL, https://api.lenco.co/access/v2)
    LENCO_SMOKE_ACCOUNT_ID  — account to debit for transfers (default: the
                              first account returned by accounts.list())
    LENCO_SMOKE_MSISDN      — mobile money number to use (default 0971111111,
                              Lenco's documented Airtel Zambia test number)
    LENCO_SMOKE_OPERATOR    — mobile money operator (default "airtel")
    SMOKE_INCLUDE_PAYMENTS  — set to "1" to also exercise
                              transfers.to_mobile_money and
                              collections.from_mobile_money (K5 each — Lenco
                              rejects mobile-money transfers below that;
                              confirmed live against production — each with
                              a unique reference). Unset by default because
                              they move real money.

Exercises the read-only endpoints (accounts, banks, resolve, transactions)
and prints the raw responses so you can inspect the real response shapes.
"""

from __future__ import annotations

import dataclasses
import json
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from lenco import LencoAPIError, LencoClient, LencoError


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip().removeprefix("export ").strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep:
            continue
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


_REPO_ROOT = Path(__file__).resolve().parent.parent
for _env_file in (".env", ".envrc"):
    _load_env_file(_REPO_ROOT / _env_file)

required = ["LENCO_API_TOKEN"]
missing = [name for name in required if not os.environ.get(name)]
if missing:
    print(
        f"Missing required environment variables: {', '.join(missing)}", file=sys.stderr
    )
    print(
        "Set them and re-run. See the header comment in utils/smoke.py.",
        file=sys.stderr,
    )
    raise SystemExit(1)

client_kwargs: dict[str, Any] = {}
if base_url := os.environ.get("LENCO_API_URL"):
    client_kwargs["base_url"] = base_url

print(f"base_url: {base_url or 'default (production)'}")

client = LencoClient(token=os.environ["LENCO_API_TOKEN"], **client_kwargs)
msisdn = os.environ.get("LENCO_SMOKE_MSISDN", "0971111111")
operator = os.environ.get("LENCO_SMOKE_OPERATOR", "airtel")

_FAILED = object()


def _to_jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            f.name: _to_jsonable(getattr(value, f.name))
            for f in dataclasses.fields(value)
        }
    if isinstance(value, list):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    return value


def _dump(value: Any) -> str:
    return json.dumps(_to_jsonable(value), indent=2, default=str).replace("\n", "\n  ")


def run(name: str, fn: Callable[[], Any]) -> Any:
    print(f"▸ {name} ... ", end="", flush=True)
    try:
        result = fn()
    except LencoAPIError as error:
        print(f"LencoAPIError — {error.message}")
        if error.status_code is not None:
            print(f"  status_code: {error.status_code}")
        if error.data is not None:
            print("  data:", _dump(error.data))
        return _FAILED
    except LencoError as error:
        print(f"LencoError — {error}")
        return _FAILED
    print("OK")
    print("  response:", _dump(result))
    return result


failures = 0

accounts_page = run("accounts.list", lambda: client.accounts.list())
if accounts_page is _FAILED:
    failures += 1
    account_id = os.environ.get("LENCO_SMOKE_ACCOUNT_ID")
else:
    account_id = os.environ.get("LENCO_SMOKE_ACCOUNT_ID") or (
        accounts_page.items[0].id if accounts_page.items else None
    )

if run("banks.list", lambda: client.banks.list(country="zm")) is _FAILED:
    failures += 1

if (
    run(
        f"resolve.mobile_money ({operator} {msisdn})",
        lambda: client.resolve.mobile_money(phone=msisdn, operator=operator),
    )
    is _FAILED
):
    failures += 1

if run("transactions.list", lambda: client.transactions.list()) is _FAILED:
    failures += 1

if account_id is not None:
    known_account_id: str = account_id
    if (
        run(
            f"accounts.balance ({known_account_id})",
            lambda: client.accounts.balance(known_account_id),
        )
        is _FAILED
    ):
        failures += 1
else:
    print(
        "Skipping accounts.balance — no account id available "
        "(set LENCO_SMOKE_ACCOUNT_ID or ensure accounts.list returns "
        "at least one account)."
    )

if os.environ.get("SMOKE_INCLUDE_PAYMENTS") == "1":
    if account_id is None:
        print("Cannot run payment operations — no account id available.")
        failures += 1
    else:
        known_account_id = account_id
        reference = f"SMOKE-{int(time.time())}"
        print(f"\nIncluding payment operations (base reference: {reference}).")
        if (
            run(
                "transfers.to_mobile_money (K5)",
                lambda: client.transfers.to_mobile_money(
                    account_id=known_account_id,
                    amount=5,
                    reference=reference,
                    phone=msisdn,
                    operator=operator,
                    country="zm",
                ),
            )
            is _FAILED
        ):
            failures += 1

        if (
            run(
                "collections.from_mobile_money (K5)",
                lambda: client.collections.from_mobile_money(
                    amount=5,
                    reference=f"{reference}-C",
                    phone=msisdn,
                    operator=operator,
                    country="zm",
                ),
            )
            is _FAILED
        ):
            failures += 1
else:
    print(
        "\nSkipping money-moving operations. Set SMOKE_INCLUDE_PAYMENTS=1 to "
        "include a 1-unit transfer and collection."
    )

client.close()

print(
    "\nSmoke test passed."
    if failures == 0
    else f"\nSmoke test finished with {failures} failure(s)."
)
raise SystemExit(0 if failures == 0 else 1)
