from rest_framework import viewsets, filters
from app.parameter.models.city_model import City
from app.parameter.serializers.city_serializer import CitySerializer
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['City'])
class CityViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CitySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    
    def get_queryset(self):
        queryset = City.objects.all().order_by('name')
        state_id = self.request.query_params.get('state')
        if state_id:
            queryset = queryset.filter(state_id=state_id)
        return queryset