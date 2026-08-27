# Transfers

Send money from your Lenco accounts to bank accounts, mobile money wallets,
Lenco Money wallets, merchant tills, or your own accounts.

::: warning
Initiation always returns HTTP 200. The `Transfer.status` field —
`"successful"`, `"pending"`, or `"failed"` — is the outcome. See
[Error handling](/guide/errors).
:::

## Initiate a transfer

Every initiation method takes `account_id` (your account UUID to debit),
`amount`, and a unique `reference`, plus either a saved
`transfer_recipient_id` **or** inline destination details.

```python
# To a bank account
transfer = client.transfers.to_bank_account(
    account_id="your-account-uuid",
    amount=20.00,
    reference="order-1001",
    account_number="9130000000000",
    bank_id="002",
    narration="Invoice 1001",  # optional
)

# To mobile money (Zambia: airtel, mtn, zamtel — Malawi: airtel, tnm)
transfer = client.transfers.to_mobile_money(
    account_id="your-account-uuid",
    amount=20.00,
    reference="order-1002",
    phone="0977433571",
    operator="airtel",
    country="zm",
)

# To a Lenco Money wallet
transfer = client.transfers.to_lenco_money(
    account_id="your-account-uuid",
    amount=20.00,
    reference="order-1003",
    wallet_number="0000001",
)

# To a Lenco merchant till
transfer = client.transfers.to_lenco_merchant(
    account_id="your-account-uuid",
    amount=20.00,
    reference="order-1004",
    till_number="0000001",
)

# Between two of your own accounts
transfer = client.transfers.to_account(
    account_id="source-account-uuid",
    credit_account_id="destination-account-uuid",
    amount=100.00,
    reference="sweep-0001",
)
```

| Parameter               | Type   | Description                                              |
| ----------------------- | ------ | -------------------------------------------------------- |
| `account_id`            | str    | Your 36-character account UUID to debit                  |
| `amount`                | float  | Amount, decimals allowed (for example `10.75`)           |
| `reference`             | str    | Unique reference — `-`, `.`, `_` and alphanumerics only  |
| `narration`             | str    | Optional narration                                       |
| `transfer_recipient_id` | str    | Optional saved recipient UUID                            |
| destination fields      | str    | Inline alternative to `transfer_recipient_id`            |

## Query transfers

```python
page = client.transfers.list(
    status="failed",
    type="mobile-money",
    from_date="2026-08-01",
    to_date="2026-08-25",
)

transfer = client.transfers.get("9525b4c6-502b-45be-90e1-81eb81a3f424")
transfer = client.transfers.get_by_reference("order-1001")
```

`get_by_reference` is how you recover from a network failure mid-initiation:
look up your reference before retrying — see [Error handling](/guide/errors#retrying-safely).

## The `Transfer` object

Notable fields: `id`, `amount`, `fee`, `currency`, `status`,
`reason_for_failure`, `reference`, `lenco_reference`, `initiated_at`,
`completed_at`, and `credit_account` (the destination, with fields populated
according to its `type`).

API details: [transfers endpoints](https://lenco-api.readme.io/v2.0/reference/get-transfers).
