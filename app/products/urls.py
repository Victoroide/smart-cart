from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import BrandViewSet, ProductCategoryViewSet, ProductViewSet, InventoryViewSet, WarrantyViewSet

router = DefaultRouter()
router.register(r'brands', BrandViewSet, basename='brands')
router.register(r'categories', ProductCategoryViewSet, basename='categories')
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'warranties', WarrantyViewSet, basename='warranties')
router.register(r'', ProductViewSet, basename='products')

urlpatterns = [
    path('', include(router.urls)),
]