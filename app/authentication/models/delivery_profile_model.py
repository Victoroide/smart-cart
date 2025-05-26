from django.db import models
from django.utils import timezone
from core.models import TimestampedModel
from app.authentication.models.user_model import User

class DeliveryProfile(TimestampedModel):
    STATUS_CHOICES = (
        ('available', 'Disponible'),
        ('busy', 'Ocupado'),
        ('offline', 'Fuera de línea'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='delivery_profile')
    identification_number = models.CharField(max_length=30, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    vehicle_type = models.CharField(max_length=50, blank=True, null=True)
    license_plate = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.get_status_display()}"
    
    def assign_delivery(self):
        self.status = 'busy'
        self.save()
    
    def mark_as_available(self):
        self.status = 'available'
        self.save()