# Retries

The SDK retries a failed `GET` automatically. `POST` never is.

## What gets retried

A `GET` is retried when it hits a connection error (refused, reset, timed
out) or gets back `429`, `500`, `502`, `503`, or `504` — 3 attempts by
default, with jittered exponential backoff (`random_between(0, min(30s,
1s * 2 ** attempt))` — "full jitter", the same default AWS SDKs and Google
Cloud client libraries use, chosen because it spreads retries out instead of
having many clients retry in lockstep during an outage). A `429`'s
`Retry-After` header overrides the formula when present — the server knows
better than a guess — but is still capped at the same 30s ceiling: a
misbehaving or malicious server sending an absurd value shouldn't be able to
hang the client.

```python
with LencoClient(token="...", max_retries=5) as client:
    ...

with LencoClient(token="...", max_retries=0) as client:  # disable retries
    ...
```

Pass your own `http_client=` (a pre-built `httpx.Client`/`httpx.AsyncClient`)
and this retry behavior is bypassed entirely — you own retries on it
yourself.

## Why POST is excluded

Lenco has no idempotency keys: it can't replay the exact response of an
earlier request the way Stripe does for a repeated `Idempotency-Key`. What it
does have is reference-level dedup — resubmitting a `reference` gets
rejected with `400 "Duplicate reference"` rather than a second transfer or
collection. That prevents a double-send, but it also means a connection
failure on the *first* `POST` attempt can surface this error on a second
attempt even though the first one succeeded. Auto-retrying `POST` would
paper over that distinction; the SDK doesn't.

Catch `LencoDuplicateReferenceError` to handle it correctly instead:

```python
from lenco import LencoDuplicateReferenceError

try:
    transfer = client.transfers.to_mobile_money(..., reference="order-1001")
except LencoDuplicateReferenceError:
    # The original request may have gone through. Find out before
    # deciding whether to send again with a new reference.
    transfer = client.transfers.get_by_reference("order-1001")
```

See [Retrying safely](/guide/errors#retrying-safely) for the full pattern,
including a plain connection failure (no response at all).
