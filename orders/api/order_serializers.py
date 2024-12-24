from rest_framework import serializers

from orders.models import CustomizationValue, Order, OrderItem, OrderStatus

class CustomizationValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomizationValue
        fields = ['customization_option', 'quantity']

class OrderItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderItem
        fields = ['cart_item', 'quantity', 'total_price']

class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = ['status', 'created_at']

class OrderSerializer(serializers.ModelSerializer):
    order_statuses = OrderStatusSerializer(many=True)  # Include the order status history

    class Meta:
        model = Order
        fields = ['order_id', 'client', 'total_price', 'order_date', 'order_time', 'order_statuses']



