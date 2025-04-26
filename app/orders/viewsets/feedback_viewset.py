from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from core.models import LoggerService
from core.pagination import CustomPagination
from app.orders.models.feedback_model import Feedback
from app.orders.models.order_model import Order
from app.products.models.product_model import Product
from app.orders.serializers.feedback_serializer import (
    FeedbackSerializer, DeliveryFeedbackSerializer, ProductFeedbackSerializer,
    UnifiedFeedbackSerializer
)
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['Feedback'])
class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all().order_by('-created_at')
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    
    def get_queryset(self):
        queryset = Feedback.objects.all()
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
            
        order_id = self.request.query_params.get('order', None)
        if order_id:
            queryset = queryset.filter(order_id=order_id)
            
        product_id = self.request.query_params.get('product', None)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
            
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'submit_feedback':
            return UnifiedFeedbackSerializer
        elif self.action == 'rate_delivery':
            return DeliveryFeedbackSerializer
        elif self.action == 'rate_product':
            return ProductFeedbackSerializer
        return FeedbackSerializer
    
    @action(detail=False, methods=['post'], url_path='submit')
    def submit_feedback(self, request):
        with transaction.atomic():
            try:
                serializer = UnifiedFeedbackSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                
                order_id = serializer.validated_data['order_id']
                order = Order.objects.get(id=order_id)
                
                if order.user != request.user and not request.user.is_staff:
                    return Response(
                        {"error": "You don't have permission to rate this order"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                delivery_feedback, created_delivery = Feedback.objects.update_or_create(
                    order=order,
                    product=None,
                    user=request.user,
                    defaults={
                        'delivery_rating': serializer.validated_data.get('delivery_rating'),
                        'delivery_comment': serializer.validated_data.get('delivery_comment', '')
                    }
                )
                
                product_feedbacks = []
                for product_data in serializer.validated_data.get('product_feedbacks', []):
                    product_id = product_data.get('product_id')
                    product = Product.objects.get(id=product_id)
                    
                    feedback, created_product = Feedback.objects.update_or_create(
                        order=order,
                        product=product,
                        user=request.user,
                        defaults={
                            'product_rating': product_data.get('product_rating'),
                            'product_comment': product_data.get('product_comment', '')
                        }
                    )
                    product_feedbacks.append(feedback)
                
                LoggerService.objects.create(
                    user=request.user,
                    action='CREATE_UPDATE',
                    table_name='Feedback',
                    description=f'Submitted unified feedback for order {order.id}'
                )
                
                result = {
                    "order_id": order.id,
                    "delivery_feedback": DeliveryFeedbackSerializer(delivery_feedback).data,
                    "product_feedbacks": ProductFeedbackSerializer(product_feedbacks, many=True).data
                }
                
                return Response(result, status=status.HTTP_200_OK)
                
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Feedback',
                    description='Error on unified feedback submission: ' + str(e)
                )
                raise e
    
    @action(detail=False, methods=['post'], url_path='rate-delivery')
    def rate_delivery(self, request):
        with transaction.atomic():
            try:
                serializer = DeliveryFeedbackSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                
                order = serializer.validated_data['order']
                
                if order.user != request.user and not request.user.is_staff:
                    return Response(
                        {"error": "You don't have permission to rate this order"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                feedback, created = Feedback.objects.update_or_create(
                    order=order,
                    product=None,
                    user=request.user,
                    defaults={
                        'delivery_rating': serializer.validated_data.get('delivery_rating'),
                        'delivery_comment': serializer.validated_data.get('delivery_comment')
                    }
                )
                
                LoggerService.objects.create(
                    user=request.user,
                    action='CREATE' if created else 'UPDATE',
                    table_name='Feedback',
                    description=f'{"Created" if created else "Updated"} delivery feedback for order {order.id}'
                )
                
                return Response(DeliveryFeedbackSerializer(feedback).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
                
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Feedback',
                    description='Error on delivery feedback: ' + str(e)
                )
                raise e
    
    @action(detail=False, methods=['post'], url_path='rate-product')
    def rate_product(self, request):
        with transaction.atomic():
            try:
                serializer = ProductFeedbackSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                
                order = serializer.validated_data['order']
                product = serializer.validated_data['product']
                
                if order.user != request.user and not request.user.is_staff:
                    return Response(
                        {"error": "You don't have permission to rate products in this order"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                exists = False
                order_items = order.items.all()
                for item in order_items:
                    if item.product.id == product.id:
                        exists = True
                        break
                        
                if not exists:
                    return Response(
                        {"error": "This product is not part of the order"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                feedback, created = Feedback.objects.update_or_create(
                    order=order,
                    product=product,
                    user=request.user,
                    defaults={
                        'product_rating': serializer.validated_data.get('product_rating'),
                        'product_comment': serializer.validated_data.get('product_comment')
                    }
                )
                
                LoggerService.objects.create(
                    user=request.user,
                    action='CREATE' if created else 'UPDATE',
                    table_name='Feedback',
                    description=f'{"Created" if created else "Updated"} product feedback for product {product.id} in order {order.id}'
                )
                
                return Response(ProductFeedbackSerializer(feedback).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
                
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Feedback',
                    description='Error on product feedback: ' + str(e)
                )
                raise e
    
    @action(detail=False, methods=['get'], url_path='order/(?P<order_id>[^/.]+)')
    def get_order_feedback(self, request, order_id=None):
        try:
            order = Order.objects.get(id=order_id)
            
            if order.user != request.user and not request.user.is_staff:
                return Response(
                    {"error": "You don't have permission to view this order's feedback"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            delivery_feedback = Feedback.objects.filter(order=order, product=None).first()
            product_feedbacks = Feedback.objects.filter(order=order).exclude(product=None)
            
            result = {
                "order_id": order.id,
                "delivery_feedback": DeliveryFeedbackSerializer(delivery_feedback).data if delivery_feedback else None,
                "product_feedbacks": ProductFeedbackSerializer(product_feedbacks, many=True).data
            }
            
            return Response(result)
            
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            LoggerService.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='ERROR',
                table_name='Feedback',
                description='Error getting order feedback: ' + str(e)
            )
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        return Response(
            {"error": "Use /feedback/submit/ endpoint to submit feedback for an order"},
            status=status.HTTP_400_BAD_REQUEST
        )