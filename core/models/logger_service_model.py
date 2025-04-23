from django.db import models
from base.settings import AUTH_USER_MODEL
from core.models.base_model import TimestampedModel

class LoggerService(TimestampedModel):
    user = models.ForeignKey(AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=50)
    table_name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    level = models.CharField(max_length=20, default='INFO')

    def save(self, *args, **kwargs):
        if self.user is None:
            self.user_id = 1
        super().save(*args, **kwargs)