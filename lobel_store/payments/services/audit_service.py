import hashlib
import json
from collections.abc import Mapping, Sequence

from payments.models import PaymentAuditEvent


class PaymentAuditService:
    """Append-only payment audit with provider data reduced to safe evidence."""

    SENSITIVE_FRAGMENTS = {
        "authorization", "api_key", "apikey", "api_token", "password",
        "secret", "session_token", "token", "card", "cvv", "cvc",
        "pan", "cookie", "email", "phone",
    }
    MAX_DEPTH = 5
    MAX_ITEMS = 50
    MAX_TEXT = 500

    @classmethod
    def record(
        cls, *, payment, event_type, from_status="", to_status="", metadata=None
    ):
        return PaymentAuditEvent.objects.create(
            payment=payment,
            event_type=str(event_type)[:50],
            from_status=str(from_status or "")[:20],
            to_status=str(to_status or "")[:20],
            metadata=cls.sanitize(metadata or {}),
        )

    @classmethod
    def provider_evidence(cls, payload):
        sanitized = cls.sanitize(payload or {})
        canonical = json.dumps(
            payload or {}, sort_keys=True, separators=(",", ":"), default=str
        ).encode()
        return {
            "filtered": sanitized,
            "payload_sha256": hashlib.sha256(canonical).hexdigest(),
        }

    @classmethod
    def sanitize(cls, value, *, depth=0):
        if depth >= cls.MAX_DEPTH:
            return "[TRUNCATED]"
        if isinstance(value, Mapping):
            result = {}
            for key, item in list(value.items())[:cls.MAX_ITEMS]:
                normalized = str(key).lower().replace("-", "_")
                if any(fragment in normalized for fragment in cls.SENSITIVE_FRAGMENTS):
                    result[str(key)] = "[REDACTED]"
                else:
                    result[str(key)] = cls.sanitize(item, depth=depth + 1)
            return result
        if isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            return [
                cls.sanitize(item, depth=depth + 1)
                for item in list(value)[:cls.MAX_ITEMS]
            ]
        if isinstance(value, (bytes, bytearray)):
            return "[BINARY]"
        if isinstance(value, str):
            return value[:cls.MAX_TEXT]
        if value is None or isinstance(value, (bool, int, float)):
            return value
        return str(value)[:cls.MAX_TEXT]
