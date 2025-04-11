from rest_framework import serializers
from .models import Brand, ProductCategory, Product, Inventory, Warranty

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = [
            'id',
            'name',
            'active',
            'created_at',
            'updated_at'
        ]

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = [
            'id',
            'name',
            'active',
            'created_at',
            'updated_at'
        ]

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id',
            'brand',
            'category',
            'name',
            'description',
            'active',
            'image_url',
            'technical_specifications',
            'price_usd',
            'price_bs',
            'created_at',
            'updated_at'
        ]

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = [
            'product',
            'stock',
            'created_at',
            'updated_at'
        ]

class WarrantySerializer(serializers.ModelSerializer):
    class Meta:
        model = Warranty
        fields = [
            'id',
            'product',
            'warranty_type',
            'details',
            'created_at',
            'updated_at'
        ]
