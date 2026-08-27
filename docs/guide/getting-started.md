# Getting started

lenco-py is an unofficial Python SDK for the [Lenco API v2](https://lenco-api.readme.io/v2.0).
This page gets you from installation to your first transfer.

## Prerequisites

- Python 3.11 or newer
- A Lenco API token — request one from <support@lenco.co>

## Installation

```bash
pip install lenco-py
```

For [card collections](/guide/card-collections), install the `card` extra:

```bash
pip install "lenco-py[card]"
```

## Create a client

::: warning
Store the token in an environment variable — never in source control. If a
token is ever exposed, contact <support@lenco.co> for a new one immediately.
:::

```python
import os
from lenco import LencoClient

client = LencoClient(token=os.environ["LENCO_API_TOKEN"])
```

Use `AsyncLencoClient` with the same arguments in async code — see
[Framework recipes](/guide/frameworks).

## Make your first transfer

Send 20 ZMW to a mobile money wallet:

```python
transfer = client.transfers.to_mobile_money(
    account_id="your-account-uuid",  # see client.accounts.list()
    amount=20.00,
    reference="order-1001",
    phone="0977433571",
    operator="airtel",
    country="zm",
)

print(transfer.status)           # "successful", "pending", or "failed"
print(transfer.lenco_reference)  # Lenco's own reference
```

::: warning
Lenco always returns HTTP 200 for transfer initiation. The HTTP status tells
you the *request* was accepted. `transfer.status` tells you the *outcome*.
See [Error handling](/guide/errors).
:::

## Choose a unique reference

`reference` is how you correlate API responses, webhooks, and status checks
with your own records. Generate one per transaction (an order ID, a UUID) and
store it before calling the API. Only `-`, `.`, `_` and alphanumeric
characters are allowed.

## Next steps

- [Handling webhooks](/guide/webhooks) — receive final transaction statuses
- [Error handling](/guide/errors) — handle failures safely
- [Framework recipes](/guide/frameworks) — Django and FastAPI
- [API reference](/reference/accounts) — every resource in detail
