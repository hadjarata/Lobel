from django.db import models
from users.models import Customer
from products.models import Product


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='orders')
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Order {self.id} - {self.customer}"

    @property
    def get_cart_total(self):
        items = self.items.all()
        return sum([item.get_total for item in items])

    @property
    def get_cart_items(self):
        items = self.items.all()
        return sum([item.quantity for item in items])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Produit supprimé'}"

    @property
    def get_total(self):
        if self.product:
            return self.product.price * self.quantity
        return 0