from rest_framework import serializers
from django.db import transaction
from .models import Order, OrderItem, Payment, Delivery
from app.products.models import Product, Inventory
from app.products.serializers import ProductSerializer
from rest_framework.exceptions import ValidationError

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    
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
        read_only_fields = ['id', 'created_at', 'updated_at']

class OrderItemCreateSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    
    class Meta:
        model = OrderItem
        fields = ['product_id', 'quantity']
    
    def validate(self, data):
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        
        try:
            product = Product.objects.get(id=product_id, active=True)
            inventory = Inventory.objects.get(product=product)
            
            if inventory.stock < quantity:
                raise ValidationError(f"Insufficient inventory for {product.name}. Available: {inventory.stock}")
                
            data['product'] = product
            return data
        except Product.DoesNotExist:
            raise ValidationError(f"Product with ID {product_id} does not exist or is not active")
        except Inventory.DoesNotExist:
            raise ValidationError(f"No inventory record found for the product with ID {product_id}")

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id',
            'order',
            'amount',
            'payment_method',
            'payment_status',
            'transaction_id',
            'payment_intent_id',
            'payment_details',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class PaymentCreateSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    payment_method = serializers.ChoiceField(choices=Payment.PAYMENT_METHOD)
    
    class Meta:
        model = Payment
        fields = ['order', 'payment_method']

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
        read_only_fields = ['id', 'created_at', 'updated_at']

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
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        
        order = Order.objects.create(
            user=user,
            total_amount=0,
            currency=validated_data['currency'],
            active=True
        )
        
        total_amount = 0
        
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            
            inventory = Inventory.objects.select_for_update().get(product=product)
            
            if inventory.stock < quantity:
                Order.objects.filter(id=order.id).delete()
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

class StripeCheckoutSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()

class PayPalCheckoutSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()

class PaymentCreateSerializer(serializers.ModelSerializer):
    payment_method = serializers.ChoiceField(choices=Payment.PAYMENT_METHOD)
    
    class Meta:
        model = Payment
        fields = [
            'order',
            'payment_method',
        ]