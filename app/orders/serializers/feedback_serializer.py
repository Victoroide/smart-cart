from rest_framework import serializers
from app.orders.models.feedback_model import Feedback
from app.orders.models.order_model import Order
from app.products.models.product_model import Product

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = [
            'id', 
            'order', 
            'product', 
            'delivery_rating', 
            'product_rating',
            'delivery_comment', 
            'product_comment',
            'user',
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class DeliveryFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = [
            'id', 
            'order',
            'delivery_rating', 
            'delivery_comment',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class ProductFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = [
            'id', 
            'order',
            'product', 
            'product_rating', 
            'product_comment',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class ProductFeedbackItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_rating = serializers.IntegerField(min_value=1, max_value=5)
    product_comment = serializers.CharField(required=False, allow_blank=True)

class UnifiedFeedbackSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    delivery_rating = serializers.IntegerField(min_value=1, max_value=5)
    delivery_comment = serializers.CharField(required=False, allow_blank=True)
    product_feedbacks = ProductFeedbackItemSerializer(many=True)
    
    def validate_order_id(self, value):
        try:
            order = Order.objects.get(id=value)
            if not hasattr(order, 'payment') or order.payment.payment_status != 'completed':
                raise serializers.ValidationError("Only completed orders can receive feedback")
            
            if not hasattr(order, 'delivery'):
                raise serializers.ValidationError("This order has no delivery information")
                
            return value
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found")
    
    def validate_product_feedbacks(self, value):
        order_id = self.initial_data.get('order_id')
        try:
            order = Order.objects.get(id=order_id)
            order_products = set()
            
            for item in order.items.all():
                order_products.add(item.product.id)
                
            for product_feedback in value:
                product_id = product_feedback.get('product_id')
                if product_id not in order_products:
                    raise serializers.ValidationError(f"Product with id {product_id} is not part of this order")
            
            return value
        except Order.DoesNotExist:
            return value