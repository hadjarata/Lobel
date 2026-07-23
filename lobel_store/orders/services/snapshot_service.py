from decimal import Decimal

from django.core.exceptions import ValidationError
from store.money import xof_integer

ORDER_CURRENCY = "XOF"


class FinancialSnapshotService:
    """Pure Decimal formulas used when commercial values are frozen."""

    @staticmethod
    def money(value) -> Decimal:
        return xof_integer(value)

    @classmethod
    def line_subtotal(cls, *, unit_price, quantity, discount_amount=Decimal("0.00")):
        unit_price = cls.money(unit_price)
        discount = cls.money(discount_amount)
        gross = unit_price * quantity
        if unit_price < 0 or quantity < 1 or discount < 0 or discount > gross:
            raise ValidationError("Montants de ligne incohérents.")
        return cls.money(gross - discount)

    @classmethod
    def order_total(cls, *, subtotal, shipping_amount, discount_amount):
        subtotal = cls.money(subtotal)
        shipping = cls.money(shipping_amount)
        discount = cls.money(discount_amount)
        if min(subtotal, shipping, discount) < 0 or discount > subtotal + shipping:
            raise ValidationError("Montants de commande incohérents.")
        return cls.money(subtotal + shipping - discount)
