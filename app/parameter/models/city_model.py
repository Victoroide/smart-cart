from django.db import models
from app.parameter.models.state_model import State

class City(models.Model):
    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='cities')
    
    def __str__(self):
        return f"{self.name}, {self.state.name}"
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Cities'