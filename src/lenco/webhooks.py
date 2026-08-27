"""Webhook signature verification and event parsing.

Lenco signs webhook payloads with an ``X-Lenco-Signature`` header: an
HMAC-SHA512 of the raw request body, keyed with the SHA256 hex digest of
your API token.

Verify every event before acting on it::

    from lenco.webhooks import verify_signature, parse_event

    @app.post("/webhooks/lenco")
    def lenco_webhook(request: Request):
        body = request.body  # raw bytes, unparsed
        verify_signature(body, request.headers["X-Lenco-Signature"], api_token)
        event = parse_event(body)
        if event.event == "collection.successful":
            ...
"""

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any, Literal

from .exceptions import LencoWebhookVerificationError

WebhookEventType = Literal[
    "transfer.successful",
    "transfer.failed",
    "collection.successful",
    "collection.failed",
    "collection.settled",
    "transaction.credit",
    "transaction.debit",
]

SIGNATURE_HEADER = "X-Lenco-Signature"


def webhook_hash_key(api_token: str) -> bytes:
    """Derive the webhook verification key from your API token.

    The key is the SHA256 hex digest of the token, per Lenco's docs.

    Args:
        api_token: Your Lenco API token (the same one used for API calls).

    Returns:
        The derived key bytes for HMAC verification.
    """
    return hashlib.sha256(api_token.encode("utf-8")).hexdigest().encode("utf-8")


def compute_signature(payload: bytes, api_token: str) -> str:
    """Compute the expected ``X-Lenco-Signature`` value for a payload.

    Args:
        payload: The raw webhook request body.
        api_token: Your Lenco API token.

    Returns:
        The hex-encoded HMAC-SHA512 signature.
    """
    return hmac.new(webhook_hash_key(api_token), payload, hashlib.sha512).hexdigest()


def verify_signature(payload: bytes, signature: str, api_token: str) -> None:
    """Verify a webhook payload's ``X-Lenco-Signature`` header.

    Args:
        payload: The raw webhook request body (unparsed bytes).
        signature: The value of the ``X-Lenco-Signature`` header.
        api_token: Your Lenco API token.

    Raises:
        LencoWebhookVerificationError: If the signature is missing or does
            not match — do not process the event.
    """
    expected = compute_signature(payload, api_token)
    if not hmac.compare_digest(expected, signature):
        raise LencoWebhookVerificationError("Invalid webhook signature")


@dataclass
class WebhookEvent:
    """A parsed webhook event.

    Attributes:
        event: The event type, e.g. ``"transfer.successful"``.
        data: The event payload as a dict (shape depends on event type).
    """

    event: str
    data: dict[str, Any]

    @classmethod
    def from_json(cls, payload: bytes | str) -> "WebhookEvent":
        """Parse a raw webhook body into an event.

        Raises:
            LencoWebhookVerificationError: If the body is not valid JSON
                or lacks the ``event`` key.
        """
        try:
            body = json.loads(payload)
            event = body["event"]
        except (ValueError, KeyError, TypeError) as exc:
            raise LencoWebhookVerificationError("Malformed webhook payload") from exc
        return cls(event=event, data=body.get("data") or {})


def parse_event(payload: bytes | str) -> WebhookEvent:
    """Parse a webhook body into a :class:`WebhookEvent`.

    Call :func:`verify_signature` first — never trust an unverified event.
    """
    return WebhookEvent.from_json(payload)
