from django.db import models
from app.parameter.models.country_model import Country

class State(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='states')
    
    def __str__(self):
        return f"{self.name}, {self.country.name}"
    
    class Meta:
        ordering = ['name']
        unique_together = ['country', 'code']