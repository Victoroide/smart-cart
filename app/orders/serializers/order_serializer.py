from rest_framework import serializers
from django.db import transaction
from app.orders.models import Order, OrderItem
from app.products.models import Product, Inventory
from app.orders.serializers.order_item_serializer import OrderItemSerializer, OrderItemCreateSerializer
from app.orders.serializers.payment_serializer import PaymentSerializer
from app.orders.serializers.delivery_serializer import DeliverySerializer
from rest_framework.exceptions import ValidationError
from services.discount_service import DiscountService
from app.authentication.serializers import UserSerializer

class DeliveryAssignmentNestedSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assignment_date = serializers.DateTimeField(read_only=True)
    delivery_person = serializers.SerializerMethodField()

    def get_delivery_person(self, obj):
        if not hasattr(obj, 'delivery_person') or obj.delivery_person is None:
            return None
        
        user = obj.delivery_person
        result = {
            'id': user.id,
            'email': user.email,
            'name': f"{user.first_name} {user.last_name}",
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'role': user.role
        }
        
        try:
            if hasattr(user, 'delivery_profile') and user.delivery_profile:
                profile = user.delivery_profile
                result.update({
                    'profile': {
                        'id': profile.id,
                        'vehicle_type': profile.vehicle_type,
                        'license_plate': profile.license_plate,
                        'status': profile.status,
                        'identification_number': profile.identification_number
                    }
                })
        except Exception:
            pass
            
        return result

class EnhancedDeliverySerializer(DeliverySerializer):
    assignment = DeliveryAssignmentNestedSerializer(read_only=True, allow_null=True)
    
    class Meta(DeliverySerializer.Meta):
        fields = DeliverySerializer.Meta.fields + ['assignment']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)
    delivery = EnhancedDeliverySerializer(read_only=True)
    user_data = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'user_data',
            'total_amount',
            'currency',
            'active',
            'discount_applied',
            'discount_percentage',
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
        user = validated_data.get('user', self.context['request'].user)
    
        if 'user' in validated_data:
            validated_data.pop('user')
        
        validated_data['total_amount'] = 0
        
        order = Order.objects.create(user=user, **validated_data)
        subtotal = 0
        
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
            
            subtotal += unit_price * quantity
        
        discount_percentage = DiscountService.get_loyalty_discount(user)
        discount_amount = (subtotal * discount_percentage) / 100
        
        order.discount_percentage = discount_percentage
        order.discount_applied = discount_amount
        order.total_amount = subtotal - discount_amount
        order.save()
        
        return order