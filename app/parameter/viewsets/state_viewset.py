from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from app.parameter.models.state_model import State
from app.parameter.serializers.state_serializer import StateSerializer, StateWithCitiesSerializer
from app.parameter.serializers.city_serializer import CitySerializer
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['State'])
class StateViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StateSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']
    
    def get_queryset(self):
        queryset = State.objects.all()
        country_id = self.request.query_params.get('country')
        if country_id:
            queryset = queryset.filter(country_id=country_id)
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StateWithCitiesSerializer
        return StateSerializer
    
    @action(detail=True, methods=['get'])
    def cities(self, request, pk=None):
        state = self.get_object()
        cities = state.cities.all()
        serializer = CitySerializer(cities, many=True)
        return Response(serializer.data)