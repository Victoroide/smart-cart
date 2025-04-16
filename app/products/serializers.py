from rest_framework import serializers
from .models import Brand, ProductCategory, Product, Inventory, Warranty
from django.db import transaction

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
        read_only_fields = ['id', 'created_at', 'updated_at']

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
        read_only_fields = ['id', 'created_at', 'updated_at']

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

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = [
            'product',
            'stock',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ProductSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    category = ProductCategorySerializer(read_only=True)
    warranty = WarrantySerializer(read_only=True)
    inventory = InventorySerializer(read_only=True)
    
    brand_id = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all(), source='brand', write_only=True)
    category_id = serializers.PrimaryKeyRelatedField(queryset=ProductCategory.objects.all(), source='category', write_only=True, required=False, allow_null=True)
    warranty_id = serializers.PrimaryKeyRelatedField(queryset=Warranty.objects.all(), source='warranty', write_only=True, required=False, allow_null=True)
    
    stock = serializers.IntegerField(write_only=True, required=False)

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
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at', 'price_bs']
    
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
        
        product = super().update(instance, validated_data)
        
        if stock is not None:
            inventory, created = Inventory.objects.update_or_create(
                product=product,
                defaults={'stock': stock}
            )
        
        return product