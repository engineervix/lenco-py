# Resolve

Verify account details before sending money — each method returns the account
holder's name so you can confirm you're paying the right person.

## Bank account

```python
resolved = client.resolve.bank_account(
    account_number="9130000000000",
    bank_id="002",           # from client.banks.list()
    country="zm",            # optional
)
print(resolved.account_name)  # "Beata Jean"
```

| Parameter        | Type | Description                          |
| ---------------- | ---- | ------------------------------------ |
| `account_number` | str  | The account number to resolve        |
| `bank_id`        | str  | The bank's Lenco ID                  |
| `country`        | str  | Optional, for example `"zm"`         |

Unknown accounts raise `LencoValidationError` ("Account details was not found").

## Mobile money

```python
resolved = client.resolve.mobile_money(
    phone="0750000000",
    operator="zamtel",   # "airtel", "mtn", or "zamtel"
)
```

Currently Zambia (`"zm"`) only.

## Lenco Money wallet

```python
resolved = client.resolve.lenco_money(wallet_number="0000001")
```

## Lenco merchant till

```python
resolved = client.resolve.lenco_merchant(till_number="0000001")
```

API details: [resolve endpoints](https://lenco-api.readme.io/v2.0/reference/resolve-bank-account).
