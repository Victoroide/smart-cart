from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from app.orders.models.delivery_address_model import DeliveryAddress
from app.orders.serializers.delivery_address_serializer import DeliveryAddressSerializer

class DeliveryAddressViewSet(viewsets.ModelViewSet):
    serializer_class = DeliveryAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return DeliveryAddress.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        address = self.get_object()
        address.is_default = True
        address.save()
        
        return Response(
            self.get_serializer(address).data,
            status=status.HTTP_200_OK
        )