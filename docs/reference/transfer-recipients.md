# Transfer recipients

Saved recipients let you transfer without repeating account details — create
once, then pass `transfer_recipient_id` to [transfers](/reference/transfers).

## List recipients

```python
page = client.transfer_recipients.list(type="mobile-money", country="zm")
```

| Parameter | Type | Description                                                  |
| --------- | ---- | ------------------------------------------------------------ |
| `page`    | int  | Result page (default `1`)                                    |
| `type`    | str  | `mobile-money`, `bank-account`, `lenco-money`, `lenco-merchant` |
| `country` | str  | 2-letter filter, for example `"zm"`                          |

## Get a recipient

```python
recipient = client.transfer_recipients.get("d6b6e00e-bdb6-43a6-a561-85b61496198e")
print(recipient.details.account_name)
```

## Create recipients

```python
# Bank account
recipient = client.transfer_recipients.create_bank_account(
    account_number="9130000000000",
    bank_id="002",
    country="zm",  # optional
)

# Mobile money (Zambia)
recipient = client.transfer_recipients.create_mobile_money(
    phone="0750000000",
    operator="zamtel",
)

# Lenco Money wallet
recipient = client.transfer_recipients.create_lenco_money(wallet_number="0000001")

# Lenco merchant till
recipient = client.transfer_recipients.create_lenco_merchant(till_number="0000001")
```

Each returns a `TransferRecipient` whose `id` you store and reuse:

```python
transfer = client.transfers.to_bank_account(
    account_id="your-account-uuid",
    amount=20.00,
    reference="order-1001",
    transfer_recipient_id=recipient.id,
)
```

API details: [transfer-recipients endpoints](https://lenco-api.readme.io/v2.0/reference/get-transfer-recipients).
