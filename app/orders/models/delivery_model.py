from django.db import models
from django.utils import timezone
from app.orders.models.order_model import Order
from app.parameter.models import Country, State, City

class Delivery(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('shipped', 'Enviado'),
        ('out_for_delivery', 'En reparto'),
        ('delivered', 'Entregado'),
        ('failed', 'Fallido'),
        ('returned', 'Devuelto'),
    )
    
    order = models.OneToOneField(
        Order, 
        on_delete=models.CASCADE, 
        related_name='delivery', 
        primary_key=True
    )
    recipient_name = models.CharField(max_length=100)
    recipient_phone = models.CharField(max_length=30)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='deliveries')
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name='deliveries')
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='deliveries')
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    delivery_status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='pending'
    )
    estimated_arrival = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)
    delivery_notes = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"Delivery for Order #{self.order_id} - {self.get_delivery_status_display()}"
    
    def full_address(self):
        address = f"{self.address_line1}"
        if self.address_line2:
            address += f", {self.address_line2}"
        address += f", {self.city.name}, {self.state.name}"
        if self.postal_code:
            address += f" {self.postal_code}"
        address += f", {self.country.name}"
        return address
    
    def mark_as_delivered(self):
        self.delivery_status = 'delivered'
        self.actual_delivery_date = timezone.now().date()
        self.save()