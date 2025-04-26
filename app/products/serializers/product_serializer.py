from rest_framework import serializers
from django.db import transaction
from app.products.models import Product, Brand, ProductCategory, Warranty, Inventory
from app.products.serializers.brand_serializer import BrandSerializer
from app.products.serializers.category_serializer import ProductCategorySerializer
from app.products.serializers.warranty_serializer import WarrantySerializer
from app.products.serializers.inventory_serializer import InventorySerializer

class ProductSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    category = ProductCategorySerializer(read_only=True)
    warranty = WarrantySerializer(read_only=True)
    inventory = InventorySerializer(read_only=True)
    
    brand_id = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all(), source='brand', write_only=True)
    category_id = serializers.PrimaryKeyRelatedField(queryset=ProductCategory.objects.all(), source='category', write_only=True, required=False, allow_null=True)
    warranty_id = serializers.PrimaryKeyRelatedField(queryset=Warranty.objects.all(), source='warranty', write_only=True, required=False, allow_null=True)
    
    stock = serializers.IntegerField(write_only=True, required=False)
    average_rating = serializers.FloatField(read_only=True)
    total_reviews = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'uuid',
            'brand',
            'brand_id',
            'category',
            'category_id',
            'warranty',
            'warranty_id',
            'inventory',
            'stock',
            'name',
            'description',
            'active',
            'image_url',
            'technical_specifications',
            'price_usd',
            'price_bs',
            'average_rating',
            'total_reviews',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at', 'price_bs', 'average_rating', 'total_reviews']
    
    def get_warranty_name(self, obj):
        return obj.warranty.name if obj.warranty else None
    
    @transaction.atomic
    def create(self, validated_data):
        stock = validated_data.pop('stock', None)
        
        product = super().create(validated_data)
        
        if stock is not None:
            Inventory.objects.create(
                product=product,
                stock=stock
            )
        
        return product
    
    @transaction.atomic
    def update(self, instance, validated_data):
        stock = validated_data.pop('stock', None)
        
        instance = super().update(instance, validated_data)
        
        if stock is not None:
            inventory, created = Inventory.objects.get_or_create(
                product=instance,
                defaults={'stock': stock}
            )
            
            if not created:
                inventory.stock = stock
                inventory.save()
        
        return instance