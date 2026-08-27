# Error handling

Every API failure raises a subclass of `LencoError`. Catch precisely, or catch
the base class as a safety net.

## Exception hierarchy

| Exception               | Raised when                                          |
| ----------------------- | ---------------------------------------------------- |
| `LencoAuthError`        | 401 — missing or invalid API token                   |
| `LencoNotFoundError`    | 404 — the resource does not exist                    |
| `LencoValidationError`  | 400/422 — the request was rejected as invalid        |
| `LencoRateLimitError`   | 429 — too many requests                              |
| `LencoServerError`      | 5xx — an error on Lenco's end                        |
| `LencoConnectionError`  | Network failure or timeout before a response         |
| `LencoAPIError`         | Any other API error (base class for the HTTP errors) |
| `LencoError`            | Base class for everything, including the above       |

Every `LencoAPIError` carries:

- `message` — the API's human-readable summary
- `status_code` — the HTTP status
- `error_code` — Lenco's optional `errorCode` field
- `data` — the raw `data` payload, when present

```python
from lenco import LencoAuthError, LencoNotFoundError, LencoValidationError, LencoError

try:
    client.resolve.bank_account(account_number="0000", bank_id="002")
except LencoValidationError as e:
    log.info("resolution failed: %s", e.message)
except LencoAuthError:
    raise  # token problem — fix config, don't retry
except LencoError as e:
    log.error("lenco call failed: %s", e)
```

## The two gotchas

::: warning HTTP 200 can still be an error
Lenco sometimes returns `200` with `{"status": false, "message": "..."}`. The
SDK treats the envelope as authoritative and raises — you never have to
check the envelope yourself.
:::

::: warning Initiation always returns 200
A `200` from transfer or collection *initiation* means the request was
*accepted*, not that money moved. Inspect the returned object's `status`:
:::

```python
transfer = client.transfers.to_mobile_money(...)

if transfer.status == "successful":
    mark_paid(transfer.reference)
elif transfer.status == "failed":
    refund_order(transfer.reference, transfer.reason_for_failure)
else:  # "pending"
    schedule_status_check(transfer.reference)
```

## Retrying safely

Lenco does not document idempotency keys. Your `reference` is the deduplication
handle: reuse the same reference when retrying a failed *request* (one that
never got a response), so you can look up the outcome with
`client.transfers.get_by_reference(reference)` before deciding to send again.

```python
try:
    transfer = client.transfers.to_mobile_money(..., reference="order-1001")
except LencoConnectionError:
    # Did it reach Lenco? Check before retrying.
    existing = client.transfers.get_by_reference("order-1001")
    ...
```
