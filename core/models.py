from django.db import models
from django.utils import timezone
from base.settings import AUTH_USER_MODEL

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


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

