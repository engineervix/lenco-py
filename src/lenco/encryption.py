"""JWE payload encryption for the Card Collection API.

Lenco requires PCI DSS–level protection for cardholder data: card
collection payloads are encrypted end-to-end as JWE compact-serialized
objects (A256GCM content encryption, RSA-OAEP-256 key wrapping) using the
RSA public key from ``GET /encryption-key``.

Requires the ``card`` extra: ``pip install lenco-py[card]``.
"""

import json
from typing import Any

from ._http import AsyncTransport, SyncTransport
from .exceptions import LencoError
from .models.collection import CardCollectionPayload


def encrypt_payload(
    payload: dict[str, Any] | CardCollectionPayload, public_key_jwk: dict[str, Any]
) -> str:
    """Encrypt a card collection payload as a JWE compact string.

    Args:
        payload: The plaintext card collection request — a
            :class:`~lenco.models.CardCollectionPayload`, or a raw dict
            (email, reference, amount, currency, customer, billing, card, …)
            for callers who need the escape hatch.
        public_key_jwk: The RSA public key (JWK dict) from
            ``GET /encryption-key``. Fetch it fresh per payload — Lenco
            may rotate the key at any time.

    Returns:
        The JWE compact-serialized payload, ready to send as
        ``{"encryptedPayload": ...}`` to ``POST /collections/card``.

    Raises:
        LencoError: If the ``card`` extra (``jwcrypto``) is not installed, or
            the key response is missing ``kid``.
    """
    try:
        from jwcrypto import jwe, jwk
    except ImportError as exc:
        raise LencoError(
            "Card encryption requires the 'card' extra: pip install lenco-py[card]"
        ) from exc

    data: dict[str, Any] = (
        payload.model_dump(mode="json", by_alias=True, exclude_none=True)
        if isinstance(payload, CardCollectionPayload)
        else payload
    )

    try:
        kid = public_key_jwk["kid"]
    except KeyError as exc:
        raise LencoError("Encryption key response is missing 'kid'") from exc

    key = jwk.JWK.from_json(json.dumps(public_key_jwk))
    protected = {
        "alg": "RSA-OAEP-256",
        "enc": "A256GCM",
        "cty": "application/json",
        "kid": kid,
    }
    token = jwe.JWE(
        json.dumps(data).encode("utf-8"),
        recipient=key,
        protected=protected,
    )
    return str(token.serialize(compact=True))


class EncryptionResource:
    """Synchronous access to ``/encryption-key`` plus payload encryption."""

    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def get_key(self) -> dict[str, Any]:
        """Fetch the current RSA public key (JWK) for payload encryption.

        Returns:
            The JWK dict (``kty``, ``n``, ``e``, ``kid``, …). Do not cache
            it — Lenco may rotate the key at any time.
        """
        envelope = self._t.request("GET", "/encryption-key")
        key: dict[str, Any] = envelope.data
        return key

    def encrypt(self, payload: dict[str, Any] | CardCollectionPayload) -> str:
        """Fetch a fresh encryption key and encrypt a card payload.

        Args:
            payload: The plaintext card collection request.

        Returns:
            The JWE compact-serialized payload.
        """
        return encrypt_payload(payload, self.get_key())


class AsyncEncryptionResource:
    """Asynchronous access to ``/encryption-key`` plus payload encryption."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def get_key(self) -> dict[str, Any]:
        """Fetch the current RSA public key (JWK) for payload encryption."""
        envelope = await self._t.request("GET", "/encryption-key")
        key: dict[str, Any] = envelope.data
        return key

    async def encrypt(self, payload: dict[str, Any] | CardCollectionPayload) -> str:
        """Fetch a fresh encryption key and encrypt a card payload."""
        return encrypt_payload(payload, await self.get_key())
