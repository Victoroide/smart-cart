from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from app.orders.models import OrderItem
from app.products.models import Inventory, Product
from app.products.serializers import ProductSerializer

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