# Collections

Request payments from customers — via mobile money prompt or by charging a
card.

## Mobile money collection

```python
collection = client.collections.from_mobile_money(
    amount=13.00,
    reference="order-5678",
    phone="0977433571",
    operator="mtn",      # Zambia: airtel, mtn, zamtel — Malawi: airtel, tnm
    country="zm",
    bearer="merchant",   # or "customer" — who pays the fee
)
```

The collection starts as `status == "pay-offline"`: the customer must approve
a prompt on their phone. Notify them, then listen for the
`collection.successful` [webhook](/guide/webhooks) or poll
`get_by_reference`.

| Parameter   | Type  | Description                                     |
| ----------- | ----- | ----------------------------------------------- |
| `amount`    | float | Amount to collect, decimals allowed             |
| `reference` | str   | Unique reference                                |
| `phone`     | str   | Customer's mobile money phone number            |
| `operator`  | str   | `airtel`, `mtn`, `zamtel` (ZM) — `airtel`, `tnm` (MW) |
| `country`   | str   | Optional — `"zm"` (Zambia) or `"mw"` (Malawi)   |
| `bearer`    | str   | Optional — `merchant` (default) or `customer`   |

::: warning
Lenco's docs list `merchant` as the default when `bearer` is omitted, but live
testing saw `customer` come back instead on one account. Pass `bearer`
explicitly if which side pays the fee matters to you.
:::

## Card collection

See [Card collections](/guide/card-collections) for the direct API. The
direct API uses JWE-encrypted payloads, and PCI DSS scope becomes your
responsibility. The result can carry a 3-D Secure redirect. For an
alternative with no PCI DSS scope, see the popup widget note at the top of
that same page.

## Verify a payment

`get_by_reference` doubles as the verification endpoint for the Lenco popup
widget: after the widget's `onSuccess` fires on your frontend, call this from
your **server** with the reference before fulfilling:

```python
collection = client.collections.get_by_reference("order-5678")
if collection.status == "successful":
    fulfill(collection.reference)
```

::: warning
Never call the Lenco API from your frontend — your secret token would be
exposed. The frontend gets results from your server.
:::

## List and get

```python
page = client.collections.list(status="successful", type="mobile-money", country="zm")
collection = client.collections.get("d7bd9ccb-0737-4e72-a387-d00454341f21")
```

The `Collection` object includes `mobile_money_details`, `bank_account_details`,
or `card_details` depending on the channel, plus `settlement` once settled.

API details: [collections endpoints](https://lenco-api.readme.io/v2.0/reference/get-collections).
