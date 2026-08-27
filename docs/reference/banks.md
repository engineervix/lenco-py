# Banks

The list of banks and financial institutions Lenco supports. Use it to look up
the `bank_id` that [resolve](/reference/resolve), [recipients](/reference/transfer-recipients),
and [transfers](/reference/transfers) take.

## List banks

```python
banks = client.banks.list(country="zm")

for bank in banks:
    print(bank.id, bank.name)
```

| Parameter | Type | Description                              |
| --------- | ---- | ---------------------------------------- |
| `country` | str  | Optional 2-letter filter, for example `"zm"` |

Returns a plain list of `Bank` objects (`id`, `name`, `country`) — no
pagination.

API details: [GET /banks](https://lenco-api.readme.io/v2.0/reference/get-banks).
