# Card collections

Charging a customer's debit/credit card involves cardholder PII, so Lenco
requires **PCI DSS compliance** on your side and encrypts the request payload
end-to-end with JWE. The SDK handles the encryption mechanics.

Requires the `card` extra:

```bash
pip install "lenco-py[card]"
```

## Flow

1. Build the plaintext payload (customer, billing, card details).
2. Encrypt it — `client.encryption.encrypt()` fetches a fresh RSA public key
   from Lenco (`GET /encryption-key`) and produces a JWE compact string
   (A256GCM content encryption, RSA-OAEP-256 key wrapping).
3. Submit it with `client.collections.from_card(encrypted_payload=...)`.
4. If the returned status is `"3ds-auth-required"`, redirect the customer to
   `result.authorization.redirect` to complete 3-D Secure.
5. The final status arrives via webhook — see [Handling webhooks](/guide/webhooks).

::: warning
Fetch the key fresh per payload (which is what `encrypt()` does). Lenco can
rotate the key at any time — do not cache it.
:::

## Example

```python
result = client.collections.from_card(
    encrypted_payload=client.encryption.encrypt({
        "email": "customer@example.com",
        "reference": "order-9012",
        "amount": 13.00,
        "currency": "ZMW",
        "customer": {"firstName": "Haim", "lastName": "Hasegawa"},
        "billing": {
            "streetAddress": "1 Independence Ave",
            "city": "Lusaka",
            "postalCode": "10101",
            "country": "ZM",
        },
        "card": {
            "number": "5555555555554444",
            "expiryMonth": "12",
            "expiryYear": "2030",
            "cvv": "123",
        },
    })
)

if result.collection.status == "3ds-auth-required":
    redirect_customer(result.authorization.redirect)
```

## Typed payload

`encrypt()` also accepts a `CardCollectionPayload`, which catches a typo'd
field name (for example, `postalCode`) at construction time instead of an
opaque 400 after encryption:

```python
from lenco.models import (
    CardCollectionBilling,
    CardCollectionCard,
    CardCollectionCustomer,
    CardCollectionPayload,
)

payload = CardCollectionPayload(
    email="customer@example.com",
    reference="order-9012",
    amount=13.00,
    currency="ZMW",
    customer=CardCollectionCustomer(first_name="Haim", last_name="Hasegawa"),
    billing=CardCollectionBilling(
        street_address="1 Independence Ave",
        city="Lusaka",
        postal_code="10101",
        country="ZM",
    ),
    card=CardCollectionCard(
        number="5555555555554444",
        expiry_month="12",
        expiry_year="2030",
        cvv="123",
    ),
)
result = client.collections.from_card(
    encrypted_payload=client.encryption.encrypt(payload)
)
```

A plain dict, as in the example above, still works — pass whichever is convenient.

## Payload fields

| Field                 | Required | Description                                        |
| --------------------- | -------- | -------------------------------------------------- |
| `email`               | Yes      | Customer email address                             |
| `reference`           | Yes      | Your unique reference (case-sensitive)             |
| `amount`              | Yes      | Amount to charge, decimals allowed (for example, `10.75`) |
| `currency`            | Yes      | ISO 3-letter code, for example `ZMW`, `USD`        |
| `bearer`              | No       | `merchant` (default) or `customer` pays the fee    |
| `customer.firstName`  | Yes      | Customer first name                                |
| `customer.lastName`   | Yes      | Customer last name                                 |
| `billing.streetAddress` | Yes    | Street address                                     |
| `billing.city`        | Yes      | City                                               |
| `billing.state`       | No       | State/province, where applicable                   |
| `billing.postalCode`  | Yes      | Postal code                                        |
| `billing.country`     | Yes      | 2-letter code, for example `ZM`                    |
| `card.number`         | Yes      | Card PAN                                           |
| `card.expiryMonth`    | Yes      | Expiry month                                       |
| `card.expiryYear`     | Yes      | Expiry year                                        |
| `card.cvv`            | Yes      | Card security code                                 |
| `redirectUrl`         | No       | Customer is redirected here after payment          |

The full parameter list and the encryption scheme are documented in
[Lenco's own docs](https://lenco-api.readme.io/v2.0/reference/initiate-collection-from-card).

## Lower-level API

If you already hold a fresh public key (for example, you batch-encrypt
several payloads in one request cycle), use `encrypt_payload` directly:

```python
from lenco.encryption import encrypt_payload

key = client.encryption.get_key()       # JWK dict with kty/n/e/kid
token = encrypt_payload(payload, key)   # JWE compact string
```
