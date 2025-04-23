from rest_framework import serializers

class StripeCheckoutSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()

class PayPalCheckoutSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()