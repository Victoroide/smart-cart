from rest_framework import serializers
from app.products.models import Warranty

class WarrantySerializer(serializers.ModelSerializer):
    brand_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Warranty
        fields = [
            'id',
            'name',
            'description',
            'duration_months',
            'brand',
            'brand_name',
            'active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_brand_name(self, obj):
        return obj.brand.name if obj.brand else None