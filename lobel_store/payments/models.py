from django.db import models

# Create your models here.
from orders.models import Order

class Payment(models.Model):
    PAYMENT_METHODS = (
        ('card', 'Card'),
        ('paypal', 'PayPal'),
        ('cash', 'Cash'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    date_paid = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.status} - {self.amount} for Order {self.order.id}"