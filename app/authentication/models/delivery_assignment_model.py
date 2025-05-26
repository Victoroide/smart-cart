from django.db import models
from django.utils import timezone
from core.models import TimestampedModel
from app.orders.models import Delivery
from app.authentication.models.user_model import User

class DeliveryAssignment(TimestampedModel):
    STATUS_CHOICES = (
        ('assigned', 'Asignado'),
        ('in_progress', 'En progreso'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    )
    
    delivery = models.OneToOneField(Delivery, on_delete=models.CASCADE, related_name='assignment')
    delivery_person = models.ForeignKey(User, on_delete=models.PROTECT, related_name='delivery_assignments', 
                                       limit_choices_to={'role': 'delivery'})
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    assignment_date = models.DateTimeField(default=timezone.now)
    start_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"Asignación #{self.id} - {self.delivery_person.first_name} {self.delivery_person.last_name}"
    
    def mark_as_in_progress(self):
        self.status = 'in_progress'
        self.start_date = timezone.now()
        self.save()
        
        self.delivery.delivery_status = 'out_for_delivery'
        self.delivery.save()
    
    def mark_as_completed(self):
        self.status = 'completed'
        self.completion_date = timezone.now()
        self.save()
        
        self.delivery.delivery_status = 'delivered'
        self.delivery.actual_delivery_date = timezone.now().date()
        self.delivery.save()
        
        if hasattr(self.delivery_person, 'delivery_profile'):
            self.delivery_person.delivery_profile.mark_as_available()