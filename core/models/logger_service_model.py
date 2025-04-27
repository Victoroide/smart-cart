from django.db import models
from base.settings import AUTH_USER_MODEL
from core.models.base_model import TimestampedModel
from core.middleware import get_current_request

class LoggerServiceManager(models.Manager):
    def create(self, **kwargs):
        if 'ip_address' not in kwargs:
            request = get_current_request()
            if request:
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')
                kwargs['ip_address'] = ip
        
        return super().create(**kwargs)

class LoggerService(TimestampedModel):
    user = models.ForeignKey(AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=50)
    table_name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    level = models.CharField(max_length=20, default='INFO')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP Address')
    
    objects = LoggerServiceManager()

    def save(self, *args, **kwargs):
        if self.user is None:
            self.user_id = 1
        super().save(*args, **kwargs)
        
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Logger Service'
        verbose_name_plural = 'Logger Services'