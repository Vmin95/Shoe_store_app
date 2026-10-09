from django.contrib import admin
from .models import Customer, Address, Category, Product, ProductVariant, Cart, CartItem, Order, OrderItem, Payment, InventoryTransaction
for model in [Customer, Address, Category, Product, ProductVariant, Cart, CartItem, Order, OrderItem, Payment, InventoryTransaction]:
    admin.site.register(model)
