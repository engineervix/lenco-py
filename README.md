# lenco-py

Unofficial Python SDK for the [Lenco API v2](https://lenco-api.readme.io/v2.0) — accounts, transfers, collections, settlements, transactions, and webhooks. Framework-agnostic: use it from Django, FastAPI, Flask, Celery, or plain scripts.

Not affiliated with or endorsed by Lenco.

[![PyPI](https://img.shields.io/pypi/v/lenco-py.svg)](https://pypi.org/project/lenco-py/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/lenco-py.svg)
![PyPI - Downloads](https://img.shields.io/pypi/dm/lenco-py.svg)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD--3--Clause-blue.svg)](LICENSE)

[![CI](https://github.com/engineervix/lenco-py/actions/workflows/ci.yml/badge.svg)](https://github.com/engineervix/lenco-py/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/engineervix/0eecb6340925b0a54b20a4048cc5a5e0/raw/covbadge.json)](https://github.com/engineervix/lenco-py/actions/workflows/ci.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

![Python](https://img.shields.io/badge/python-%233670A0.svg?style=for-the-badge&logo=python&logoColor=ffdd54)
![Pydantic](https://img.shields.io/badge/pydantic-%23E92063.svg?style=for-the-badge&logo=pydantic&logoColor=white)
![Pytest](https://img.shields.io/badge/pytest-%23ffffff.svg?style=for-the-badge&logo=pytest&logoColor=2f9fe3)
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Installation](#installation)
- [Quickstart](#quickstart)
- [Async (FastAPI)](#async-fastapi)
- [Django](#django)
- [Webhooks](#webhooks)
- [Card collections (PCI DSS)](#card-collections-pci-dss)
- [Phone normalization](#phone-normalization)
- [Error handling](#error-handling)
- [Retries](#retries)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

**Documentation: https://engineervix.github.io/lenco-py/**

- Sync and async clients with identical resource APIs
- Fully typed (mypy strict), pydantic v2 models
- Webhook signature verification with the standard library only
- JWE card-payload encryption as an optional extra
- Automatic retry with jittered backoff for transient failures — GET only, never POST
- Zambian phone number normalization as an optional extra

## Installation

```bash
pip install lenco-py
pip install "lenco-py[card]"    # adds jwcrypto for card collections
pip install "lenco-py[phone]"   # adds phonenumbers for phone normalization
```

## Quickstart

```python
from lenco import LencoClient

with LencoClient(token="your-api-token") as client:
    # Accounts
    for account in client.accounts.list().items:
        print(account.id, account.currency, account.available_balance)

    balance = client.accounts.balance("b176cda5-7d97-4a3f-b4dd-ab0234e9e08c")

    # Verify a recipient before sending money
    resolved = client.resolve.bank_account(account_number="9130000000000", bank_id="002")
    print(resolved.account_name)  # "Beata Jean"

    # Send money (mobile money — Zambia)
    transfer = client.transfers.to_mobile_money(
        account_id="your-account-uuid",
        amount=20.00,
        reference="order-1234",       # unique per transfer
        phone="0977433571",
        operator="airtel",
        country="zm",
    )
    # Transfers always return HTTP 200 — inspect the status:
    assert transfer.status == "successful", transfer.reason_for_failure
```

## Async (FastAPI)

```python
from fastapi import FastAPI
from lenco import AsyncLencoClient

app = FastAPI()
client = AsyncLencoClient(token="your-api-token")

@app.post("/payments/request")
async def request_payment(phone: str, amount: float):
    collection = await client.collections.from_mobile_money(
        amount=amount,
        reference="order-5678",
        phone=phone,
        operator="mtn",
        country="zm",
        bearer="merchant",
    )
    # status is "pay-offline" until the customer approves on their phone
    return {"reference": collection.reference, "status": collection.status}
```

## Django

```python
# payments/services.py
from lenco import LencoClient
from django.conf import settings

def charge_mobile_money(phone: str, operator: str, amount: float, reference: str):
    with LencoClient(token=settings.LENCO_API_TOKEN) as client:
        return client.collections.from_mobile_money(
            amount=amount,
            reference=reference,
            phone=phone,
            operator=operator,
            country="zm",
        )
```

For long-running use, prefer instantiating one client at module level and reusing it (the underlying httpx client pools connections).

## Webhooks

Lenco signs every webhook with `X-Lenco-Signature` (HMAC-SHA512 of the raw body, keyed by the SHA256 of your API token). Always verify before processing:

```python
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from lenco.exceptions import LencoWebhookVerificationError
from lenco.webhooks import parse_event, verify_signature

@csrf_exempt
def lenco_webhook(request: HttpRequest):
    try:
        verify_signature(
            request.body,
            request.headers["X-Lenco-Signature"],
            api_token=settings.LENCO_API_TOKEN,
        )
    except LencoWebhookVerificationError:
        return JsonResponse({"detail": "invalid signature"}, status=400)

    event = parse_event(request.body)
    if event.event == "collection.successful":
        fulfill_order(event.data["reference"])
    elif event.event == "transfer.failed":
        alert_ops(event.data)

    # Always ack quickly — Lenco retries every 30 min for 24 h otherwise.
    return JsonResponse({"ok": True})
```

Event types: `transfer.successful`, `transfer.failed`, `collection.successful`, `collection.failed`, `collection.settled`, `transaction.credit`, `transaction.debit`.

## Card collections (PCI DSS)

Card payloads are JWE-encrypted end-to-end. The SDK fetches a fresh RSA key per payload (Lenco rotates keys):

```python
from lenco import LencoClient

with LencoClient(token="...") as client:
    encrypted = client.encryption.encrypt({
        "email": "customer@example.com",
        "reference": "order-9012",
        "amount": 13.00,
        "currency": "ZMW",
        "customer": {"firstName": "Haim", "lastName": "Hasegawa"},
        "billing": {
            "streetAddress": "1 Independence Ave",
            "city": "Lusaka",
            "postalCode": "10101",
            "country": "ZM",
        },
        "card": {
            "number": "5555555555554444",
            "expiryMonth": "12",
            "expiryYear": "2030",
            "cvv": "123",
        },
    })
    result = client.collections.from_card(encrypted_payload=encrypted)

if result.collection.status == "3ds-auth-required":
    redirect_customer(result.authorization.redirect)
```

`encrypt()` also accepts a typed `CardCollectionPayload` instead of a dict, so a typo'd field name fails at construction instead of as an opaque 400 — see [Card collections](https://engineervix.github.io/lenco-py/guide/card-collections).

## Phone normalization

Lenco's mobile money APIs expect a Zambian number in local `0XXXXXXXXX` shape. `normalize_zambian_phone()` gets you there from `+260...`, `260...`, or a spaced local number, and rejects anything that isn't a valid Zambian mobile number (including landlines):

```python
from lenco.phone import normalize_zambian_phone

normalize_zambian_phone("+260966123456")  # "0966123456"
normalize_zambian_phone("0211234567")     # ValueError — landline, not mobile
```

It's standalone — no client involved — so call it wherever you collect a phone number. See [Phone normalization](https://engineervix.github.io/lenco-py/guide/phone-normalization).

## Error handling

```python
from lenco import LencoAuthError, LencoNotFoundError, LencoValidationError, LencoError

try:
    client.resolve.bank_account(account_number="0000", bank_id="002")
except LencoValidationError as e:
    print(e.message)          # "Account details was not found"
except LencoAuthError:
    # 401 — check your token
    ...
except LencoNotFoundError:
    # 404
    ...
except LencoError:
    # network failure, 5xx, anything else
    ...
```

Note the envelope gotcha: Lenco can return HTTP 200 with `{"status": false}`. The SDK treats that as an error and raises — you never have to check the envelope yourself. But for **transfer and collection initiation**, a `200` with `"status": true` means the request was *accepted*. The outcome lives in `transfer.status` / `collection.status` (`"successful"`, `"pending"`, `"failed"`, `"pay-offline"`, …).

## Retries

A failed `GET` — a connection error, or a `429`/`5xx` response — is retried automatically: 3 attempts by default, jittered exponential backoff, honoring `Retry-After` on a `429`.

```python
with LencoClient(token="...", max_retries=5) as client:
    ...

with LencoClient(token="...", max_retries=0) as client:  # disable retries
    ...
```

`POST` (transfer/collection initiation, card charges) is **never** auto-retried — Lenco has no idempotency keys, so a blind retry risks a second transfer instead of a safe re-read. Catch `LencoDuplicateReferenceError` to retry one safely yourself — see [Retrying safely](https://engineervix.github.io/lenco-py/guide/errors#retrying-safely) and [Retries](https://engineervix.github.io/lenco-py/guide/retries).

## Development

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest              # test suite (mocked transport, no network)
mypy src            # strict type checking
ruff check src      # lint
black src tests     # format
lefthook install    # one-time: run ruff/black/mypy on commit, lint commit messages
```

Docs (VitePress, Node 22+ and [`just`](https://github.com/casey/just) — `docs/` has its own `package.json`, wrapped by the root `justfile`):

```bash
just docs-install
just docs-dev      # local dev server
just docs-build    # production build
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

BSD-3-Clause. See [LICENSE](LICENSE).
