# Transactions

Every credit and debit that occurred on your accounts — the ledger view.

## List transactions

```python
page = client.transactions.list(
    type="debit",                            # or "credit"
    account_id="b176cda5-7d97-4a3f-b4dd-ab0234e9e08c",
    from_date="2026-08-01",
    to_date="2026-08-25",
    search="Transfer",
)

for txn in page.items:
    print(txn.datetime, txn.type, txn.amount, txn.currency, txn.balance)
```

| Parameter    | Type | Description                        |
| ------------ | ---- | ---------------------------------- |
| `page`       | int  | Result page (default `1`)          |
| `type`       | str  | `credit` or `debit`                |
| `from_date`  | str  | `YYYY-MM-DD`                       |
| `to_date`    | str  | `YYYY-MM-DD`                       |
| `search`     | str  | Free-text search term              |
| `account_id` | str  | Filter by account UUID             |

## Get a transaction

```python
txn = client.transactions.get("d6730fe6-77a0-4432-a283-832eaef31786")
```

Fields: `id`, `amount`, `currency`, `narration`, `type` (`credit`/`debit`),
`datetime`, `account_id`, and `balance` (the account balance after the
transaction).

API details: [transactions endpoints](https://lenco-api.readme.io/v2.0/reference/get-transactions).
