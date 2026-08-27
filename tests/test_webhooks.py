"""Webhook signature verification tests.

Expected signatures are computed independently in this module from the
documented algorithm (SHA256 of the token as key, HMAC-SHA512 of the raw
body) so a regression in the SDK implementation cannot silently pass.
"""

import hashlib
import hmac
import json

import pytest

from lenco.exceptions import LencoWebhookVerificationError
from lenco.webhooks import compute_signature, parse_event, verify_signature

API_TOKEN = "my-secret-lenco-token"

PAYLOAD = json.dumps(
    {
        "event": "transfer.successful",
        "data": {"id": "9525b4c6-502b-45be-90e1-81eb81a3f424", "amount": "20.00"},
    }
).encode("utf-8")

# Independent recomputation of the documented algorithm.
EXPECTED_SIGNATURE = hmac.new(
    hashlib.sha256(API_TOKEN.encode()).hexdigest().encode(),
    PAYLOAD,
    hashlib.sha512,
).hexdigest()


class TestVerifySignature:
    def test_valid_signature_passes(self) -> None:
        verify_signature(PAYLOAD, EXPECTED_SIGNATURE, API_TOKEN)  # no exception

    def test_wrong_signature_rejected(self) -> None:
        with pytest.raises(LencoWebhookVerificationError):
            verify_signature(PAYLOAD, "0" * 128, API_TOKEN)

    def test_tampered_payload_rejected(self) -> None:
        tampered = PAYLOAD.replace(b"20.00", b"99999.00")
        with pytest.raises(LencoWebhookVerificationError):
            verify_signature(tampered, EXPECTED_SIGNATURE, API_TOKEN)

    def test_wrong_token_rejected(self) -> None:
        with pytest.raises(LencoWebhookVerificationError):
            verify_signature(PAYLOAD, EXPECTED_SIGNATURE, "different-token")

    def test_compute_signature_matches_documented_algorithm(self) -> None:
        assert compute_signature(PAYLOAD, API_TOKEN) == EXPECTED_SIGNATURE


class TestParseEvent:
    def test_parses_event(self) -> None:
        event = parse_event(PAYLOAD)
        assert event.event == "transfer.successful"
        assert event.data["amount"] == "20.00"

    def test_rejects_malformed_body(self) -> None:
        with pytest.raises(LencoWebhookVerificationError):
            parse_event(b"not json")

    def test_rejects_body_without_event_key(self) -> None:
        with pytest.raises(LencoWebhookVerificationError):
            parse_event(json.dumps({"data": {}}))
