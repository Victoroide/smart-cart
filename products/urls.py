from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BrandViewSet, ProductCategoryViewSet, ProductViewSet, InventoryViewSet, WarrantyViewSet

router = DefaultRouter()
router.register(r'brands', BrandViewSet, basename='brand')
router.register(r'categories', ProductCategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'warranty', WarrantyViewSet, basename='warranty')

urlpatterns = [
    path('', include(router.urls)),
]
