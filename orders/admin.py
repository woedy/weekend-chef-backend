from django.contrib import admin

from orders.models import CartItem, Cart, Order, OrderItem, OrderPayment, OrderRating, OrderStatus, ShoppingList
from orders.models import CustomizationValue

admin.site.register(Cart)
admin.site.register(CustomizationValue)
admin.site.register(CartItem)

admin.site.register(Order)
admin.site.register(OrderStatus)
admin.site.register(OrderItem)
admin.site.register(OrderPayment)
admin.site.register(OrderRating)
admin.site.register(ShoppingList)
