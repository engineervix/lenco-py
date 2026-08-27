# Accounts

Your Lenco bank accounts and their balances. All methods are available on both
`LencoClient` (sync) and `AsyncLencoClient` (async, awaited).

## List accounts

```python
page = client.accounts.list(page=1)

for account in page.items:
    print(account.id, account.currency, account.available_balance)

page.meta.total         # total records across all pages
page.meta.current_page
```

| Parameter | Type | Description                    |
| --------- | ---- | ------------------------------ |
| `page`    | int  | Result page (default `1`)      |

`Account` fields: `id`, `type`, `status`, `currency`, `available_balance`,
`ledger_balance`, `created_at`, and `details` (with `details.type`,
`details.account_name`, `details.till_number`).

## Get an account

```python
account = client.accounts.get("b176cda5-7d97-4a3f-b4dd-ab0234e9e08c")
```

Raises `LencoNotFoundError` if the ID doesn't exist.

## Get an account's balance

```python
balance = client.accounts.balance("b176cda5-7d97-4a3f-b4dd-ab0234e9e08c")
print(balance.available_balance, balance.currency)
```

API details: [accounts endpoints](https://lenco-api.readme.io/v2.0/reference/get-accounts).
