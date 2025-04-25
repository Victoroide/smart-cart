from rest_framework import serializers
from app.authentication.models import CustomerLoyalty

class CustomerLoyaltySerializer(serializers.ModelSerializer):
    discount_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomerLoyalty
        fields = ['user', 'tier', 'total_orders', 'total_spent', 'points', 'last_order_date', 'discount_percentage']
        read_only_fields = ['user', 'total_orders', 'total_spent', 'points', 'last_order_date', 'discount_percentage']
    
    def get_discount_percentage(self, obj):
        return obj.get_discount_percentage()