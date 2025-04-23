from django.db import models
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
    technical_specifications = models.TextField(null=True, blank=True)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_bs = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.price_usd is not None:
            rate = getattr(settings, 'USD_TO_BS_RATE', 13)
            self.price_bs = self.price_usd * rate
            
        super().save(*args, **kwargs)