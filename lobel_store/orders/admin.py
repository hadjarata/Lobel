from django.contrib import admin

# Register your models here.
from .models import Order, OrderItem, Customer

admin.site.register(Order)
admin.site.register(OrderItem)
