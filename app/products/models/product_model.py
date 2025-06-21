from django.db import models
from django.db.models import Avg
import uuid
from core.models import TimestampedModel
from base.storage import PublicMediaStorage
from base import settings
from app.products.models.brand_model import Brand
from app.products.models.category_model import ProductCategory
from app.products.models.warranty_model import Warranty

class Product(TimestampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    warranty = models.ForeignKey(Warranty, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)
    image_url = models.FileField(storage=PublicMediaStorage(custom_path='products/images'), null=True, blank=True)

    model_3d_url = models.FileField(storage=PublicMediaStorage(custom_path='products/3d_models'), null=True, blank=True)
    ar_url = models.FileField(storage=PublicMediaStorage(custom_path='products/ar_models'), null=True, blank=True)

    model_3d_format = models.CharField(max_length=10, null=True, blank=True, help_text="Format of 3D model (e.g., glb, gltf, obj)")
    supports_ar = models.BooleanField(default=False, help_text="Whether this product has AR support")
    technical_specifications = models.TextField(null=True, blank=True)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_bs = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.price_usd is not None:
            rate = getattr(settings, 'USD_TO_BS_RATE', 13)
            self.price_bs = self.price_usd * rate
            
        if self.ar_url and not self.supports_ar:
            self.supports_ar = True
            
        if self.model_3d_url and not self.model_3d_format:
            filename = self.model_3d_url.name.lower()
            if filename.endswith('.glb'):
                self.model_3d_format = 'glb'
            elif filename.endswith('.gltf'):
                self.model_3d_format = 'gltf'
            elif filename.endswith('.obj'):
                self.model_3d_format = 'obj'
            elif filename.endswith('.usdz'):
                self.model_3d_format = 'usdz'
                
        super().save(*args, **kwargs)

    @property
    def average_rating(self):
        from app.orders.models.feedback_model import Feedback
        avg = Feedback.objects.filter(product=self, product_rating__isnull=False).aggregate(avg=Avg('product_rating'))['avg']
        return round(avg, 1) if avg else None
    
    @property
    def total_reviews(self):
        from app.orders.models.feedback_model import Feedback
        return Feedback.objects.filter(product=self, product_rating__isnull=False).count()