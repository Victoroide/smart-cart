from rest_framework import serializers
from app.orders.models import Payment, Order

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