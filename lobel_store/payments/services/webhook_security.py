import hashlib
import ipaddress
from dataclasses import dataclass

from django.conf import settings
from django.utils import timezone


class WebhookAuthenticationError(Exception):
    pass


@dataclass(frozen=True)
class AuthenticatedWebhook:
    signature_verified: bool
    authentication_method: str
    provider_event_id: str
    source_ip_hash: str


class WebhookSecurityService:
    def authenticate(
        self, *, provider, raw_body, headers, payload, source_ip
    ) -> AuthenticatedWebhook:
        self._validate_source_ip(source_ip)
        result = provider.verify_webhook_authenticity(
            raw_body, headers or {}, payload
        )
        required = bool(
            getattr(settings, "PAYMENT_WEBHOOK_SIGNATURE_REQUIRED", False)
        )
        if required:
            if not result.verification_implemented:
                raise WebhookAuthenticationError(
                    "Webhook signature verification is not implemented."
                )
            if not result.verified:
                raise WebhookAuthenticationError("Invalid webhook signature.")
            if not result.event_id:
                raise WebhookAuthenticationError(
                    "Authenticated webhook event ID is missing."
                )
            if result.occurred_at is None or not timezone.is_aware(
                result.occurred_at
            ):
                raise WebhookAuthenticationError(
                    "Authenticated webhook timestamp is missing."
                )
            maximum_age = getattr(
                settings, "PAYMENT_WEBHOOK_MAX_AGE_SECONDS", 300
            )
            age = abs((timezone.now() - result.occurred_at).total_seconds())
            if age > maximum_age:
                raise WebhookAuthenticationError(
                    "Webhook timestamp is outside the accepted window."
                )
        return AuthenticatedWebhook(
            signature_verified=bool(result.verified),
            authentication_method=(
                result.method if result.verified else "remote_verification"
            )[:50],
            provider_event_id=(
                str(result.event_id)[:255] if result.verified and result.event_id else ""
            ),
            source_ip_hash=(
                hashlib.sha256(source_ip.encode()).hexdigest()
                if source_ip else ""
            ),
        )

    @staticmethod
    def _validate_source_ip(source_ip):
        allowed = getattr(settings, "PAYMENT_WEBHOOK_ALLOWED_IPS", [])
        if not allowed:
            return
        try:
            address = ipaddress.ip_address(source_ip)
            networks = [
                ipaddress.ip_network(value, strict=False) for value in allowed
            ]
        except (TypeError, ValueError) as exc:
            raise WebhookAuthenticationError(
                "Webhook source IP cannot be validated."
            ) from exc
        if not any(address in network for network in networks):
            raise WebhookAuthenticationError("Webhook source IP is not allowed.")
