from rest_framework import serializers

from chef.models import ChefProfile
from clients.models import Client
from dispatch.models import DispatchDriver
from orders.models import Order, OrderItem, OrderPayment, OrderStatus

# Order Item Serializer
class OrderItemSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'cart', 'quantity', 'total_price']

    def get_total_price(self, obj):
        return obj.total_price()

# Order Payment Serializer
class OrderPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderPayment
        fields = ['payment_method', 'amount', 'created_at']

# Client Serializer
class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'user', 'user__username', 'user__first_name', 'user__last_name']

# Chef Serializer
class ChefSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChefProfile
        fields = ['id', 'user', 'user__username', 'user__first_name', 'user__last_name']

# Dispatch Driver Serializer
class DispatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispatchDriver
        fields = ['id', 'user', 'user__username', 'user__first_name', 'user__last_name']


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = ['status', 'created_at']



# Main Order Serializer
class OrderDetailSerializer(serializers.ModelSerializer):
    client = ClientSerializer()
    chef = ChefSerializer()
    dispatch = DispatchSerializer()
    order_items = OrderItemSerializer(many=True)
    payments = OrderPaymentSerializer(many=True)
    order_statuses = OrderStatusSerializer(many=True)  # Include order status history
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'order_date', 'order_time', 'total_price', 'paid',
            'delivery_date', 'delivery_time', 'delivery_fee', 'tax', 'location_name', 'digital_address',
            'lat', 'lng', 'client', 'chef', 'dispatch', 'order_items', 'payments', 'order_statuses'
        ]

    def get_total_price(self, obj):
        # Calculate total price based on the sum of each item in the order
        return sum(item.total_price() for item in obj.items.all())
