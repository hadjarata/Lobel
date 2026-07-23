from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError


XOF_INTEGER_ERROR = "Les montants XOF doivent être des nombres entiers."


def validate_xof_integer(value):
    if value is None:
        return
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError("Montant XOF invalide.") from exc
    if not amount.is_finite() or amount != amount.to_integral_value():
        raise ValidationError(XOF_INTEGER_ERROR, code="xof_fraction_not_allowed")


def xof_integer(value) -> Decimal:
    amount = Decimal(value)
    validate_xof_integer(amount)
    return amount
