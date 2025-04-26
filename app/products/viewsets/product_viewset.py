from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db import transaction

from core.models import LoggerService
from core.pagination import CustomPagination
from app.products.models import Product
from app.products.serializers import ProductSerializer

from services.pinecone_service import PineconeService
from services.recommendation_service import RecommendationService

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['Products'])
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

    @extend_schema(
        request=ProductSerializer,
        responses={201: ProductSerializer},
        description="Create a new product with optional image upload. Use multipart/form-data to upload files.",
        examples=[
            OpenApiExample(
                'Product Example',
                summary='Basic product creation',
                value={
                    "name": "Smartphone XYZ",
                    "brand": 1,
                    "category": 2,
                    "warranty": 3,
                    "stock": 100,
                    "price_usd": 699.99,
                    "description": "A high-end smartphone with excellent features.",
                    "active": True,
                    "technical_specifications": "6.5-inch display, 128GB storage, 5G support"
                },
                request_only=True,
            )
        ],
        tags=['Products']
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
                
    @extend_schema(
        request=ProductSerializer,
        responses={200: ProductSerializer},
        description="Update a product with optional image upload. Use multipart/form-data to upload files.",
        examples=[
            OpenApiExample(
                'Product Update Example',
                summary='Basic product update',
                value={
                    "name": "Updated Smartphone XYZ",
                    "price_usd": 899.99
                },
                request_only=True,
            )
        ],
        tags=['Products']
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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='query',
                type=str,
                description='Search query for product name or description',
                required=True
            ),
            OpenApiParameter(
                name='count',
                type=int,
                description='Number of similar products to return',
                required=False,
                default=5
            )
        ],
        responses={200: ProductSerializer(many=True)},
        description="Get similar products based on a search query. Returns a list of products sorted by similarity score.",
        examples=[
            OpenApiExample(
                'Similar Products Example',
                summary='Get similar products',
                value={
                    "query": "Smartphone",
                    "count": 5
                },
                request_only=True,
            )
        ],
        tags=['Products']
    )
    @action(detail=False, methods=['get'])
    def similar(self, request):
        query = request.query_params.get('query', '')
        count = int(request.query_params.get('count', '5'))
        
        if not query:
            return Response({"error": "Query parameter is required"}, status=400)
        
        try:
            recommendation_service = RecommendationService()
            vector_results = recommendation_service.get_similar_products(query, top_k=count)
            
            if not vector_results:
                return Response([])
                
            product_uuids = []
            similarity_scores = {}
            
            for item in vector_results:
                if 'id' in item:
                    uuid_value = item['id']
                else:
                    uuid_value = item.get('vector_id')
                    
                if uuid_value:
                    product_uuids.append(uuid_value)
                    similarity_scores[uuid_value] = item.get('score', 0)
            
            products = Product.objects.filter(
                uuid__in=product_uuids, 
                active=True
            ).select_related('brand', 'category', 'warranty')
            
            products = sorted(
                products, 
                key=lambda p: product_uuids.index(str(p.uuid))
            )
            
            serializer = ProductSerializer(products, many=True)
            result_data = serializer.data
            
            for item in result_data:
                uuid_str = item.get('uuid')
                if uuid_str in similarity_scores:
                    item['similarity_score'] = similarity_scores[uuid_str]
            
            return Response(result_data)
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
        
    @action(detail=True, methods=['get'], url_path='reviews')
    def product_reviews(self, request, pk=None):
        product = self.get_object()
        from app.orders.models.feedback_model import Feedback
        
        feedbacks = Feedback.objects.filter(
            product=product, 
            product_rating__isnull=False
        ).order_by('-created_at')
        
        page = self.paginate_queryset(feedbacks)
        if page is not None:
            from app.orders.serializers.feedback_serializer import ProductFeedbackSerializer
            serializer = ProductFeedbackSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        from app.orders.serializers.feedback_serializer import ProductFeedbackSerializer
        serializer = ProductFeedbackSerializer(feedbacks, many=True)
        return Response(serializer.data)