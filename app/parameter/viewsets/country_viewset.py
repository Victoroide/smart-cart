from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from app.parameter.models.country_model import Country
from app.parameter.serializers.country_serializer import CountrySerializer, CountryWithStatesSerializer
from app.parameter.serializers.state_serializer import StateSerializer
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['Country'])
class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.all().order_by('name')
    serializer_class = CountrySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CountryWithStatesSerializer
        return CountrySerializer
    
    @action(detail=True, methods=['get'])
    def states(self, request, pk=None):
        country = self.get_object()
        states = country.states.all()
        serializer = StateSerializer(states, many=True)
        return Response(serializer.data)