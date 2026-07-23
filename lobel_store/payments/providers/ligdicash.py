import json
import logging
from decimal import Decimal
from typing import Any
from urllib import error, parse, request

from django.conf import settings

from .base import (
    CheckoutContext,
    CheckoutSessionResult,
    PaymentAPIError,
    PaymentCommunicationError,
    PaymentConfigurationError,
    PaymentInvalidResponseError,
    PaymentProvider,
    PaymentVerificationResult,
    WebhookParseError,
)

logger = logging.getLogger(__name__)


class LigdicashProvider(PaymentProvider):
    provider_name = "ligdicash"
    webhook_signature_supported = False

    CREATE_PATH = "/pay/v01/redirect/checkout-invoice/create"
    CONFIRM_PATH = "/pay/v01/redirect/checkout-invoice/confirm"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_token: str | None = None,
        base_url: str | None = None,
        store_name: str | None = None,
        store_url: str | None = None,
        return_url: str | None = None,
        cancel_url: str | None = None,
        callback_url: str | None = None,
        timeout: int | None = None,
    ):
        self.api_key = api_key if api_key is not None else settings.LIGDICASH_API_KEY
        self.api_token = api_token if api_token is not None else settings.LIGDICASH_API_TOKEN
        self.base_url = (
            base_url if base_url is not None else settings.LIGDICASH_BASE_URL
        ).rstrip("/")
        self.store_name = store_name if store_name is not None else settings.LIGDICASH_STORE_NAME
        self.store_url = store_url if store_url is not None else settings.LIGDICASH_STORE_URL
        self.return_url = return_url if return_url is not None else settings.LIGDICASH_RETURN_URL
        self.cancel_url = cancel_url if cancel_url is not None else settings.LIGDICASH_CANCEL_URL
        self.callback_url = (
            callback_url if callback_url is not None else settings.LIGDICASH_CALLBACK_URL
        )
        self.timeout = timeout if timeout is not None else settings.LIGDICASH_HTTP_TIMEOUT

    def create_checkout(self, context: CheckoutContext) -> CheckoutSessionResult:
        self._validate_configuration()

        payload = self._build_create_payload(context)
        logger.info(
            "[Payment] checkout created - provider=%s payment_id=%s order_id=%s amount=%s",
            self.provider_name,
            context.payment.id,
            context.order.id,
            context.amount,
        )

        response = self._post_json(self.CREATE_PATH, payload)
        return self._parse_create_response(response, context)

    def verify_payment(
        self,
        session_token: str,
        *,
        payment=None,
    ) -> PaymentVerificationResult:
        self._validate_configuration()

        params = parse.urlencode({"invoiceToken": session_token})
        url = f"{self.base_url}{self.CONFIRM_PATH}?{params}"
        response = self._get_json(url)

        status = str(response.get("status", "pending")).lower()
        response_code = str(response.get("response_code", ""))
        external_transaction_id = response.get("request_id") or response.get("external_id")
        invoice = response.get("invoice") if isinstance(response.get("invoice"), dict) else {}
        custom_data = response.get("custom_data")
        entries = self._normalize_custom_data(custom_data)
        amount = invoice.get("total_amount", response.get("total_amount"))
        currency = invoice.get("devise", response.get("devise", "XOF"))
        provider_reference = (
            invoice.get("external_id") or response.get("external_id")
            or entries.get("transaction_id")
        )

        logger.info(
            "[Payment] payment verified - provider=%s token=%s status=%s response_code=%s",
            self.provider_name,
            session_token[:12] + "..." if len(session_token) > 12 else session_token,
            status,
            response_code,
        )

        return PaymentVerificationResult(
            status=status,
            response_code=response_code,
            external_transaction_id=str(external_transaction_id) if external_transaction_id else None,
            raw=response,
            provider=self.provider_name,
            provider_reference=str(provider_reference) if provider_reference else (
                payment.order_reference if payment and status != "completed" else None
            ),
            verified_amount=Decimal(str(amount)) if amount is not None else (
                Decimal(payment.amount) if payment and status != "completed" else None
            ),
            verified_currency=str(currency) if currency else None,
            verification_implemented=True,
        )

    def parse_webhook(self, raw_body: bytes, content_type: str | None) -> dict:
        if not raw_body:
            raise WebhookParseError("Empty webhook body.")

        normalized_type = (content_type or "").lower()

        if "application/json" in normalized_type:
            return self._parse_json_body(raw_body)

        if "application/x-www-form-urlencoded" in normalized_type:
            return self._parse_form_body(raw_body)

        try:
            return self._parse_json_body(raw_body)
        except WebhookParseError:
            return self._parse_form_body(raw_body)

    def extract_payment_id(self, payload: dict) -> int | None:
        custom_data = payload.get("custom_data")
        entries = self._normalize_custom_data(custom_data)

        for key in ("payment_id", "transaction_id"):
            value = entries.get(key)
            if not value:
                continue

            payment_id = self._parse_payment_id(value)
            if payment_id is not None:
                return payment_id

        return None

    def build_deduplication_key(self, payload: dict, payload_hash: str) -> str:
        request_id = payload.get("request_id")
        if request_id:
            return f"ligdicash:request:{request_id}"

        status = payload.get("status", "")
        transaction_id = payload.get("transaction_id", "")
        if status and transaction_id:
            return f"ligdicash:logical:{status}:{transaction_id}"

        return f"ligdicash:hash:{payload_hash}"

    def _build_create_payload(self, context: CheckoutContext) -> dict[str, Any]:
        items = []
        for order_item in context.order.items.all():
            unit_price = self.format_amount(order_item.unit_price)
            line_total = unit_price * order_item.quantity
            items.append(
                {
                    "name": order_item.product_name,
                    "description": order_item.variant_name or order_item.product_name,
                    "quantity": order_item.quantity,
                    "unit_price": unit_price,
                    "total_price": line_total,
                }
            )

        if context.order.shipping_amount:
            shipping = self.format_amount(context.order.shipping_amount)
            items.append({
                "name": "Livraison", "description": context.order.delivery_method_label,
                "quantity": 1, "unit_price": shipping, "total_price": shipping,
            })
        return {
            "commande": {
                "invoice": {
                    "items": items,
                    "total_amount": context.amount,
                    "devise": context.currency,
                    "description": context.description,
                    "customer": "",
                    "customer_firstname": context.customer_firstname,
                    "customer_lastname": context.customer_lastname,
                    "customer_email": context.customer_email,
                    "external_id": context.order_reference,
                    "otp": "",
                },
                "store": {
                    "name": self.store_name,
                    "website_url": self.store_url,
                },
                "actions": {
                    "cancel_url": self.cancel_url,
                    "return_url": self.return_url,
                    "callback_url": self.callback_url,
                },
                "custom_data": {
                    "transaction_id": f"LOBEL-PAYMENT-{context.payment.id}",
                    "payment_id": str(context.payment.id),
                    "order_id": str(context.order.id),
                    "order_reference": context.order_reference,
                },
            }
        }

    def _parse_create_response(
        self,
        data: dict[str, Any],
        context: CheckoutContext,
    ) -> CheckoutSessionResult:
        response_code = str(data.get("response_code", ""))
        if response_code != "00":
            message = data.get("response_text") or data.get("description") or "Erreur LigdiCash."
            raise PaymentAPIError(f"LigdiCash a rejeté la requête: {message}")

        token = data.get("token")
        payment_url = data.get("response_text")

        if not isinstance(token, str) or not token:
            raise PaymentInvalidResponseError("Réponse LigdiCash incomplète: token manquant.")

        if not isinstance(payment_url, str) or not payment_url:
            raise PaymentInvalidResponseError(
                "Réponse LigdiCash incomplète: response_text (URL de paiement) manquant."
            )

        return CheckoutSessionResult(
            payment_url=payment_url,
            session_token=token,
            amount=context.amount,
            currency=context.currency,
            order_reference=context.order_reference,
        )

    def _validate_configuration(self) -> None:
        missing = []
        if not self.api_key:
            missing.append("LIGDICASH_API_KEY")
        if not self.api_token:
            missing.append("LIGDICASH_API_TOKEN")
        if not self.base_url:
            missing.append("LIGDICASH_BASE_URL")
        if not self.return_url:
            missing.append("LIGDICASH_RETURN_URL")
        if not self.cancel_url:
            missing.append("LIGDICASH_CANCEL_URL")
        if not self.callback_url:
            missing.append("LIGDICASH_CALLBACK_URL")

        if missing:
            raise PaymentConfigurationError(
                f"Configuration LigdiCash manquante: {', '.join(missing)}"
            )
        if self.timeout <= 0:
            raise PaymentConfigurationError("LIGDICASH_HTTP_TIMEOUT doit être positif.")
        if not getattr(settings, "LIGDICASH_VERIFY_TLS", True):
            raise PaymentConfigurationError("La vérification TLS LigdiCash est obligatoire.")

    def _headers(self) -> dict[str, str]:
        return {
            "Apikey": self.api_key,
            "Authorization": f"Bearer {self.api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            url,
            data=body,
            headers=self._headers(),
            method="POST",
        )
        return self._execute_request(http_request)

    def _get_json(self, url: str) -> dict[str, Any]:
        http_request = request.Request(url, headers=self._headers(), method="GET")
        return self._execute_request(http_request)

    def _execute_request(self, http_request: request.Request) -> dict[str, Any]:
        try:
            with request.urlopen(http_request, timeout=self.timeout) as response:
                response_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise PaymentAPIError(f"LigdiCash a rejeté la requête: {details}") from exc
        except error.URLError as exc:
            raise PaymentCommunicationError(
                f"Impossible de contacter LigdiCash: {exc.reason}"
            ) from exc
        except TimeoutError as exc:
            raise PaymentCommunicationError("Délai dépassé lors de l'appel LigdiCash.") from exc

        try:
            parsed_response = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise PaymentInvalidResponseError("Réponse LigdiCash non JSON.") from exc

        if not isinstance(parsed_response, dict):
            raise PaymentInvalidResponseError("Réponse LigdiCash invalide.")

        return parsed_response

    def _parse_json_body(self, raw_body: bytes) -> dict:
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise WebhookParseError("Payload webhook JSON invalide.") from exc

        if not isinstance(payload, dict):
            raise WebhookParseError("Payload webhook JSON invalide.")

        return payload

    def _parse_form_body(self, raw_body: bytes) -> dict:
        try:
            parsed = parse.parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
        except UnicodeDecodeError as exc:
            raise WebhookParseError("Payload webhook form invalide.") from exc

        payload = {key: values[0] if len(values) == 1 else values for key, values in parsed.items()}

        custom_data = payload.get("custom_data")
        if isinstance(custom_data, str):
            try:
                payload["custom_data"] = json.loads(custom_data)
            except json.JSONDecodeError:
                pass

        return payload

    def _normalize_custom_data(self, custom_data: Any) -> dict[str, str]:
        if isinstance(custom_data, dict):
            return {str(key): str(value) for key, value in custom_data.items()}

        if not isinstance(custom_data, list):
            return {}

        entries: dict[str, str] = {}
        for item in custom_data:
            if not isinstance(item, dict):
                continue
            key = item.get("keyof_customdata")
            value = item.get("valueof_customdata")
            if key and value is not None:
                entries[str(key)] = str(value)

        return entries

    def _parse_payment_id(self, value: str) -> int | None:
        cleaned = value.strip()
        if cleaned.isdigit():
            return int(cleaned)

        prefix = "LOBEL-PAYMENT-"
        if cleaned.startswith(prefix):
            suffix = cleaned[len(prefix) :]
            if suffix.isdigit():
                return int(suffix)

        return None
