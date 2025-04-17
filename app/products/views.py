from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.db import transaction
from core.models import LoggerService
from core.pagination import CustomPagination
from .models import *
from .serializers import *
from services.pinecone_service import PineconeService
from services.openai_service import OpenAIService
from services.recommendation_service import RecommendationService
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.filter(active=True)
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().create(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='CREATE',
                    table_name='Brand',
                    description='Created brand ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Brand',
                    description='Error on create brand: ' + str(e)
                )
                raise e

    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().partial_update(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='PATCH',
                    table_name='Brand',
                    description='Partially updated brand ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Brand',
                    description='Error on partial_update brand: ' + str(e)
                )
                raise e

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                instance = self.get_object()
                instance.active = False
                instance.save()
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='DELETE',
                    table_name='Brand',
                    description='Soft-deleted brand ' + str(instance.id)
                )
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Brand',
                    description='Error on delete brand: ' + str(e)
                )
                raise e

class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.filter(active=True)
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().create(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='CREATE',
                    table_name='ProductCategory',
                    description='Created category ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='ProductCategory',
                    description='Error on create category: ' + str(e)
                )
                raise e

    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().partial_update(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='PATCH',
                    table_name='ProductCategory',
                    description='Partially updated category ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='ProductCategory',
                    description='Error on partial_update category: ' + str(e)
                )
                raise e

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                instance = self.get_object()
                instance.active = False
                instance.save()
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='DELETE',
                    table_name='ProductCategory',
                    description='Soft-deleted category ' + str(instance.id)
                )
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='ProductCategory',
                    description='Error on delete category: ' + str(e)
                )
                raise e

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(active=True).order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [
        MultiPartParser, 
        FormParser, 
        JSONParser
    ]
    pagination_class = CustomPagination

    filterset_fields = ['brand', 'category']
    search_fields = ['name', 'description']

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Product name'),
                'brand': openapi.Schema(type=openapi.TYPE_INTEGER, description='Brand ID'),
                'category': openapi.Schema(type=openapi.TYPE_INTEGER, description='Category ID'),
                'warranty': openapi.Schema(type=openapi.TYPE_INTEGER, description='Warranty ID'),
                'stock': openapi.Schema(type=openapi.TYPE_INTEGER, description='Available inventory quantity'),
                'price_usd': openapi.Schema(type=openapi.TYPE_NUMBER, description='Price in USD'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Product description'),
                'active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Product status'),
                'technical_specifications': openapi.Schema(type=openapi.TYPE_STRING, description='Technical specifications'),
            },
            example={
                "name": "Smartphone XYZ",
                "brand": 1,
                "category": 2,
                "warranty": 3,
                "stock": 100,
                "price_usd": 699.99,
                "description": "A high-end smartphone with excellent features.",
                "active": True,
                "technical_specifications": "6.5-inch display, 128GB storage, 5G support"
            }
        ),
        operation_description="Create a new product with optional image upload. Use multipart/form-data to upload files.",
        consumes=['multipart/form-data', 'application/json']
    )
    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                data = request.data.copy()
                image_file = None

                if 'image_url' in request.FILES:
                    image_file = request.FILES.get('image_url')
                    if 'image_url' in data:
                        del data['image_url']

                serializer = self.get_serializer(data=data)
                serializer.is_valid(raise_exception=True)
                instance = serializer.save()

                if image_file:
                    try:
                        instance.image_url = image_file
                        instance.save(update_fields=['image_url'])
                    except Exception as img_error:
                        LoggerService.objects.create(
                            user=request.user if request.user.is_authenticated else None,
                            action='ERROR',
                            table_name='Product',
                            description=f'Error saving image for product {instance.id}: {str(img_error)}'
                        )

                try:
                    pinecone_service = PineconeService()
                    pinecone_service.upsert_product(instance)
                except Exception as e:
                    LoggerService.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        action='ERROR',
                        table_name='Product',
                        description=f'Error syncing product {instance.id} with Pinecone: {str(e)}'
                    )

                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='CREATE',
                    table_name='Product',
                    description='Created product ' + str(instance.id)
                )

                serializer = self.get_serializer(instance)
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Product',
                    description='Error on create product: ' + str(e)
                )
                raise e
                
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Product name'),
                'brand_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Brand ID'),
                'category_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Category ID'),
                'warranty_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Warranty ID'),
                'stock': openapi.Schema(type=openapi.TYPE_INTEGER, description='Available inventory quantity'),
                'price_usd': openapi.Schema(type=openapi.TYPE_NUMBER, description='Price in USD'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Product description'),
                'active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Product status'),
                'technical_specifications': openapi.Schema(type=openapi.TYPE_STRING, description='Technical specifications'),
            },
            example={
                "name": "Updated Smartphone XYZ",
                "price_usd": 899.99
            }
        ),
        operation_description="Update a product with optional image upload. Use multipart/form-data to upload files.",
        consumes=['multipart/form-data', 'application/json']
    )
    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                instance = self.get_object()
                
                original_image = instance.image_url
                
                image_file = request.FILES.get('image_url')
                data = request.data.copy()
                
                if 'image_url' in data:
                    del data['image_url']
                    
                serializer = self.get_serializer(instance, data=data, partial=True)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                
                if image_file:
                    try:
                        instance.image_url = image_file
                        instance.save(update_fields=['image_url'])
                    except Exception as img_error:
                        instance.image_url = original_image
                        instance.save(update_fields=['image_url'])
                        LoggerService.objects.create(
                            user=request.user if request.user.is_authenticated else None,
                            action='ERROR',
                            table_name='Product',
                            description=f'Error saving image for product {instance.id}: {str(img_error)}'
                        )
                
                try:
                    pinecone_service = PineconeService()
                    pinecone_service.upsert_product(instance)
                except Exception as e:
                    LoggerService.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        action='ERROR',
                        table_name='Product',
                        description=f'Error syncing updated product {instance.id} to Pinecone: {str(e)}'
                    )
                
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='PATCH',
                    table_name='Product',
                    description='Partially updated product ' + str(instance.id)
                )
                
                updated_serializer = self.get_serializer(instance)
                return Response(updated_serializer.data)
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Product',
                    description='Error on partial_update product: ' + str(e)
                )
                raise e

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                instance = self.get_object()
                
                try:
                    pinecone_service = PineconeService()
                    pinecone_service.delete_product(instance.uuid)
                except Exception as e:
                    LoggerService.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        action='ERROR',
                        table_name='Product',
                        description=f'Error removing product {instance.id} from Pinecone: {str(e)}'
                    )
                
                instance.active = False
                instance.save()
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='DELETE',
                    table_name='Product',
                    description='Soft-deleted product ' + str(instance.id)
                )
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Product',
                    description='Error on delete product: ' + str(e)
                )
                raise e

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'query', 
                openapi.IN_QUERY, 
                description="Search term to find similar products", 
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'count', 
                openapi.IN_QUERY, 
                description="Number of similar products to return", 
                type=openapi.TYPE_INTEGER,
                default=5
            ),
        ],
        responses={
            200: openapi.Response('List of similar products', ProductSerializer(many=True)),
            400: openapi.Response('Bad Request', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ))
        },
        operation_description="Find products similar to the search query"
    )
    @action(detail=False, methods=['get'])
    def similar(self, request):
        query = request.query_params.get('query', '')
        count = int(request.query_params.get('count', '5'))
        
        if not query:
            return Response({"error": "Query parameter is required"}, status=400)
        
        try:
            recommendation_service = RecommendationService()
            similar_products = recommendation_service.get_similar_products(query, top_k=count)
            return Response(similar_products)
        except Exception as e:
            LoggerService.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='ERROR',
                table_name='Product',
                description=f'Error getting similar products: {str(e)}'
            )
            return Response({"error": "Error processing request"}, status=500)
    
            
    @action(detail=False, methods=['post'])
    def sync_all_to_pinecone(self, request):
        if not request.user.is_staff:
            return Response({"error": "Not authorized"}, status=403)
            
        try:
            products = Product.objects.filter(active=True)
            pinecone_service = PineconeService()
            
            successful = 0
            failed = 0
            
            for product in products:
                try:
                    result = pinecone_service.upsert_product(product)
                    if result:
                        successful += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1
            
            LoggerService.objects.create(
                user=request.user,
                action='SYNC',
                table_name='Product',
                description=f'Synced {successful} products to Pinecone. Failed: {failed}'
            )
            
            return Response({
                "message": f"Synced {successful} products to Pinecone. Failed: {failed}",
                "successful": successful,
                "failed": failed
            })
        except Exception as e:
            LoggerService.objects.create(
                user=request.user,
                action='ERROR',
                table_name='Product',
                description=f'Error syncing all products to Pinecone: {str(e)}'
            )
            return Response({"error": f"Error syncing products: {str(e)}"}, status=500)

class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().create(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='CREATE',
                    table_name='Inventory',
                    description='Created inventory ' + str(response.data.get('product'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Inventory',
                    description='Error on create inventory: ' + str(e)
                )
                raise e

    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().partial_update(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='PATCH',
                    table_name='Inventory',
                    description='Partially updated inventory ' + str(response.data.get('product'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Inventory',
                    description='Error on partial_update inventory: ' + str(e)
                )
                raise e

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                instance = self.get_object()
                instance.delete()
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='DELETE',
                    table_name='Inventory',
                    description='Deleted inventory ' + str(instance.product_id)
                )
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Inventory',
                    description='Error on delete inventory: ' + str(e)
                )
                raise e

class WarrantyViewSet(viewsets.ModelViewSet):
    queryset = Warranty.objects.filter(active=True)
    serializer_class = WarrantySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    
    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().create(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='CREATE',
                    table_name='Warranty',
                    description='Created warranty ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Warranty',
                    description='Error on create warranty: ' + str(e)
                )
                raise e

    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().partial_update(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='PATCH',
                    table_name='Warranty',
                    description='Partially updated warranty ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Warranty',
                    description='Error on partial_update warranty: ' + str(e)
                )
                raise e

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                instance = self.get_object()
                instance.active = False
                instance.save()
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='DELETE',
                    table_name='Warranty',
                    description='Soft-deleted warranty ' + str(instance.id)
                )
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Warranty',
                    description='Error on delete warranty: ' + str(e)
                )
                raise e