from django.urls import path, include
from rest_framework.routers import DefaultRouter
from app.orders.viewsets import *
from app.orders.viewsets.payment_views import StripeCheckoutView, PayPalCheckoutView, PaymentStatusView
from app.orders.webhooks import stripe_webhook, paypal_webhook

router = DefaultRouter()
router.register(r'order-items', OrderItemViewSet)
router.register(r'delivery-addresses', DeliveryAddressViewSet, basename='delivery-addresses')
router.register(r'deliveries', DeliveryViewSet, basename='delivery')
router.register(r'finance', OrderViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'feedback', FeedbackViewSet, basename='feedback')

urlpatterns = [
    path('', include(router.urls)),
    path('stripe-checkout/', StripeCheckoutView.as_view(), name='stripe-checkout'),
    path('paypal-checkout/', PayPalCheckoutView.as_view(), name='paypal-checkout'),
    path('payment-status/<int:order_id>/', PaymentStatusView.as_view(), name='payment-status'),
    path('webhooks/stripe/', stripe_webhook, name='stripe-webhook'),
    path('webhooks/paypal/', paypal_webhook, name='paypal-webhook'),
]