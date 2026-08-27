# Handling webhooks

Lenco notifies your server about events — a transfer completing, a collection
settling — by POSTing JSON to a webhook URL you configure on your account.

## Verify every event

Every event carries an `X-Lenco-Signature` header: an HMAC-SHA512 of the raw
request body, keyed with the SHA256 hex digest of your API token. Verification
uses only the Python standard library — no extra dependencies:

```python
from lenco.webhooks import verify_signature, parse_event
from lenco.exceptions import LencoWebhookVerificationError

def handle_request(body: bytes, signature: str) -> None:
    try:
        verify_signature(body, signature, api_token=os.environ["LENCO_API_TOKEN"])
    except LencoWebhookVerificationError:
        # reject — do not process
        return

    event = parse_event(body)
    ...
```

::: warning
Verify against the **raw request body** — the exact bytes received, before any
JSON parsing. Parsing and re-serialising can change whitespace and key order,
which breaks the signature. In Django, use `request.body`. In FastAPI, use
`await request.body()`.
:::

## Event types

| Event                   | Meaning                                            |
| ----------------------- | -------------------------------------------------- |
| `transfer.successful`   | A transfer from one of your accounts completed     |
| `transfer.failed`       | A transfer you attempted failed                    |
| `collection.successful` | A collection completed                             |
| `collection.failed`     | A collection failed                                |
| `collection.settled`    | Your account was credited for a collection         |
| `transaction.credit`    | An account linked to your token was credited       |
| `transaction.debit`     | An account linked to your token was debited        |

`parse_event` returns a `WebhookEvent` with `event.event` (the type string)
and `event.data` (the payload dict, shaped like the corresponding resource —
for example, a transfer object for `transfer.*` events).

## Respond quickly

Lenco considers any response outside `200`/`201`/`202` unacknowledged and
retries every 30 minutes for 24 hours. If processing is slow, acknowledge
immediately and do the work asynchronously (for example, enqueue a Celery
task), and make your handler idempotent — a redelivered event must be
harmless.

## Example (Django)

```python
import os
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
            api_token=os.environ["LENCO_API_TOKEN"],
        )
    except LencoWebhookVerificationError:
        return JsonResponse({"detail": "invalid signature"}, status=400)

    event = parse_event(request.body)
    if event.event == "collection.successful":
        fulfill_order.delay(event.data["reference"])  # Celery task

    return JsonResponse({"ok": True})
```

For FastAPI, see [Framework recipes](/guide/frameworks#fastapi).
