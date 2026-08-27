# Framework recipes

The SDK is plain Python with no framework coupling. These recipes show
idiomatic wiring per framework. In every case: construct one client and reuse
it (the underlying httpx client pools connections), and keep the token in
environment variables.

## Django

Use the synchronous `LencoClient`. A module-level client works for sync views.
Create it once and reuse it.

```python
# payments/lenco.py
import os
from lenco import LencoClient

lenco = LencoClient(token=os.environ["LENCO_API_TOKEN"])
```

```python
# payments/services.py
from .lenco import lenco

def request_mobile_money_payment(*, phone: str, operator: str, amount: float, reference: str):
    return lenco.collections.from_mobile_money(
        amount=amount,
        reference=reference,
        phone=phone,
        operator=operator,
        country="zm",
        bearer="merchant",
    )
```

Webhook view:

```python
# payments/views.py
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

::: tip
Celery tasks also use the sync client. Instantiate one per task module, or
share a single module-level client.
:::

## FastAPI

Use `AsyncLencoClient`. Create it during application startup and close it on
shutdown via the lifespan handler:

```python
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from lenco import AsyncLencoClient

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.lenco = AsyncLencoClient(token=os.environ["LENCO_API_TOKEN"])
    yield
    await app.state.lenco.aclose()

app = FastAPI(lifespan=lifespan)
```

```python
@app.post("/payments/request")
async def request_payment(request: Request, phone: str, amount: float):
    lenco: AsyncLencoClient = request.app.state.lenco
    collection = await lenco.collections.from_mobile_money(
        amount=amount,
        reference="order-5678",
        phone=phone,
        operator="mtn",
        country="zm",
        bearer="merchant",
    )
    # "pay-offline" until the customer approves on their phone
    return {"reference": collection.reference, "status": collection.status}
```

Webhook route — note the raw body read before parsing:

```python
from fastapi import HTTPException
from lenco.exceptions import LencoWebhookVerificationError
from lenco.webhooks import parse_event, verify_signature

@app.post("/webhooks/lenco")
async def lenco_webhook(request: Request):
    body = await request.body()
    try:
        verify_signature(
            body,
            request.headers["x-lenco-signature"],
            api_token=os.environ["LENCO_API_TOKEN"],
        )
    except LencoWebhookVerificationError:
        raise HTTPException(status_code=400, detail="invalid signature")

    event = parse_event(body)
    if event.event == "transfer.failed":
        await alert_ops(event.data)

    return {"ok": True}
```
