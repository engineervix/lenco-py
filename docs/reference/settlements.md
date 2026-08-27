# Settlements

Settlements are the credits to your account for completed collections. Each
settlement includes the source collection.

## List settlements

```python
page = client.settlements.list(
    status="settled",          # or "pending"
    type="instant",            # or "next-day"
    collection_type="mobile-money",
    from_date="2026-08-01",
    to_date="2026-08-25",
)

for s in page.items:
    print(s.amount_settled, s.currency, s.collection.reference)
```

| Parameter         | Type | Description                                  |
| ----------------- | ---- | -------------------------------------------- |
| `page`            | int  | Result page (default `1`)                    |
| `from_date`       | str  | `YYYY-MM-DD`                                 |
| `to_date`         | str  | `YYYY-MM-DD`                                 |
| `status`          | str  | `pending` or `settled`                       |
| `type`            | str  | `instant` or `next-day`                      |
| `collection_type` | str  | `card`, `mobile-money`, or `bank-account`    |
| `country`         | str  | 2-letter filter, for example `"zm"`          |

## Get a settlement

```python
settlement = client.settlements.get("c04583d7-d026-4dfa-b8b5-e96f17f93bb8")
```

Fields: `id`, `amount_settled`, `currency`, `status`, `type`, `account_id`,
`created_at`, `settled_at`, and `collection` (the full source `Collection`).

API details: [settlements endpoints](https://lenco-api.readme.io/v2.0/reference/get-settlements).
