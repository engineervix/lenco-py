"""Card encryption tests: JWE round-trip and the encryption-key endpoint."""

import json

import pytest
import respx
from conftest import BASE_URL, TOKEN
from httpx import Response

from lenco import AsyncLencoClient, LencoClient
from lenco.exceptions import LencoError

jwcrypto = pytest.importorskip("jwcrypto")
from jwcrypto import jwe, jwk  # noqa: E402

# Generate a real RSA keypair for the test: the public JWK goes to the SDK,
# the private key decrypts the result to prove the JWE is well-formed.
_key = jwk.JWK.generate(kty="RSA", size=2048, kid="test-key-1")
PUBLIC_JWK = json.loads(_key.export_public())
PRIVATE_JWK = json.loads(_key.export_private())

CARD_PAYLOAD = {
    "email": "customer@example.com",
    "reference": "ref-1",
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
}


class TestEncryptPayload:
    def test_round_trip(self) -> None:
        from lenco.encryption import encrypt_payload

        token = encrypt_payload(CARD_PAYLOAD, PUBLIC_JWK)

        decrypted = jwe.JWE()
        decrypted.deserialize(token, key=_key)
        assert json.loads(decrypted.payload.decode()) == CARD_PAYLOAD

    def test_jose_headers_match_spec(self) -> None:
        from lenco.encryption import encrypt_payload

        token = encrypt_payload(CARD_PAYLOAD, PUBLIC_JWK)

        header = jwe.JWE.from_jose_token(token).jose_header
        assert header["alg"] == "RSA-OAEP-256"
        assert header["enc"] == "A256GCM"
        assert header["cty"] == "application/json"
        assert header["kid"] == "test-key-1"


class TestTypedPayload:
    def test_matches_dict_payload_field_for_field(self) -> None:
        """A typed CardCollectionPayload must encrypt to the same wire bytes as
        the equivalent raw dict — same camelCase keys, no null keys included."""
        from lenco.encryption import encrypt_payload
        from lenco.models import (
            CardCollectionBilling,
            CardCollectionCard,
            CardCollectionCustomer,
            CardCollectionPayload,
        )

        payload = CardCollectionPayload(
            email="customer@example.com",
            reference="ref-1",
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

        token = encrypt_payload(payload, PUBLIC_JWK)

        decrypted = jwe.JWE()
        decrypted.deserialize(token, key=_key)
        assert json.loads(decrypted.payload.decode()) == CARD_PAYLOAD


class TestMissingKid:
    def test_raises_lenco_error_not_key_error(self) -> None:
        from lenco.encryption import encrypt_payload

        key_without_kid = {k: v for k, v in PUBLIC_JWK.items() if k != "kid"}

        with pytest.raises(LencoError, match="kid"):
            encrypt_payload(CARD_PAYLOAD, key_without_kid)


class TestEncryptionResource:
    @respx.mock
    def test_encrypt_accepts_typed_payload(self) -> None:
        from lenco.models import (
            CardCollectionBilling,
            CardCollectionCard,
            CardCollectionCustomer,
            CardCollectionPayload,
        )

        respx.get(f"{BASE_URL}/encryption-key").mock(
            return_value=Response(
                200, json={"status": True, "message": "", "data": PUBLIC_JWK}
            )
        )
        payload = CardCollectionPayload(
            email="customer@example.com",
            reference="ref-1",
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

        with LencoClient(token=TOKEN) as client:
            token = client.encryption.encrypt(payload)

        decrypted = jwe.JWE()
        decrypted.deserialize(token, key=_key)
        assert json.loads(decrypted.payload.decode()) == CARD_PAYLOAD

    @respx.mock
    def test_fetches_key_and_encrypts(self) -> None:
        respx.get(f"{BASE_URL}/encryption-key").mock(
            return_value=Response(
                200, json={"status": True, "message": "", "data": PUBLIC_JWK}
            )
        )

        with LencoClient(token=TOKEN) as client:
            token = client.encryption.encrypt(CARD_PAYLOAD)

        decrypted = jwe.JWE()
        decrypted.deserialize(token, key=_key)
        assert json.loads(decrypted.payload.decode()) == CARD_PAYLOAD

    @respx.mock
    async def test_async_fetches_key_and_encrypts(self) -> None:
        respx.get(f"{BASE_URL}/encryption-key").mock(
            return_value=Response(
                200, json={"status": True, "message": "", "data": PUBLIC_JWK}
            )
        )

        async with AsyncLencoClient(token=TOKEN) as client:
            token = await client.encryption.encrypt(CARD_PAYLOAD)

        assert token.count(".") == 4  # JWE compact serialization: 5 parts
