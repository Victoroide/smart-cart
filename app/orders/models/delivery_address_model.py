from django.db import models
from django.conf import settings
from app.parameter.models import Country, State, City

class DeliveryAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='delivery_addresses')
    address_name = models.CharField(max_length=100)
    recipient_name = models.CharField(max_length=100)
    recipient_phone = models.CharField(max_length=30)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='delivery_addresses')
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name='delivery_addresses')
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='delivery_addresses')
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    is_default = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.address_name} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            DeliveryAddress.objects.filter(
                user=self.user, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
            
        super().save(*args, **kwargs)
    
    def full_address(self):
        address = f"{self.address_line1}"
        if self.address_line2:
            address += f", {self.address_line2}"
        address += f", {self.city.name}, {self.state.name}"
        if self.postal_code:
            address += f" {self.postal_code}"
        address += f", {self.country.name}"
        return address

    class Meta:
        ordering = ['-is_default', 'address_name']