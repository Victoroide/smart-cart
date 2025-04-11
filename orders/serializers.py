from rest_framework import serializers
from .models import Order, OrderItem, Payment, Delivery

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'order',
            'product',
            'quantity',
            'unit_price',
            'created_at',
            'updated_at'
        ]

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id',
            'order',
            'amount',
            'method',
            'status',
            'transaction_id',
            'created_at',
            'updated_at'
        ]

class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = [
            'id',
            'order',
            'delivery_address',
            'delivery_status',
            'tracking_info',
            'estimated_arrival',
            'created_at',
            'updated_at'
        ]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)
    delivery = DeliverySerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'total_amount',
            'currency',
            'status',
            'payment_method',
            'active',
            'items',
            'payment',
            'delivery',
            'created_at',
            'updated_at'
        ]
