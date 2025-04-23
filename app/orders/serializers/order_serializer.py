from rest_framework import serializers
from django.db import transaction
from app.orders.models import Order, OrderItem
from app.products.models import Product, Inventory
from app.orders.serializers.order_item_serializer import OrderItemSerializer, OrderItemCreateSerializer
from app.orders.serializers.payment_serializer import PaymentSerializer
from app.orders.serializers.delivery_serializer import DeliverySerializer
from rest_framework.exceptions import ValidationError

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
            'active',
            'items',
            'payment',
            'delivery',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True)
    currency = serializers.ChoiceField(choices=[('USD', 'USD'), ('BS', 'BS')])
    
    class Meta:
        model = Order
        fields = ['currency', 'items']
        
    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        
        validated_data['total_amount'] = 0
        
        order = Order.objects.create(**validated_data)
        total_amount = 0
        
        processed_products = set()
        
        for item_data in items_data:
            product_id = item_data.pop('product_id')
            
            if product_id in processed_products:
                continue
                
            processed_products.add(product_id)
            
            product = Product.objects.get(id=product_id)
            quantity = item_data['quantity']
            
            inventory = Inventory.objects.select_for_update().get(product=product)
            if inventory.stock < quantity:
                raise ValidationError(f"Insufficient inventory for {product.name}. Available: {inventory.stock}")
                
            unit_price = product.price_usd if order.currency == 'USD' else product.price_bs
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=unit_price
            )
            
            inventory.stock -= quantity
            inventory.save()
            
            total_amount += unit_price * quantity
        
        order.total_amount = total_amount
        order.save()
        
        return order