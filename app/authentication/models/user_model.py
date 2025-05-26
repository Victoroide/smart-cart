from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from core.models import TimestampedModel

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        
        if extra_fields.get('role') == 'admin':
            extra_fields['is_staff'] = True
            extra_fields['is_superuser'] = True
        
        if 'active' in extra_fields:
            extra_fields['is_active'] = extra_fields['active']
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('active', True)
        extra_fields.setdefault('is_active', True)
        
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser, TimestampedModel):
    ROLES = [
        ('admin', 'Admin'),
        ('customer', 'Customer'),
        ('delivery', 'Delivery'),
    ]
    
    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(max_length=10, choices=ROLES, default='customer')
    active = models.BooleanField(default=True)
    phone = models.CharField(max_length=30, null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()
    
    def save(self, *args, **kwargs):
        if self.role == 'admin':
            self.is_staff = True
            self.is_superuser = True
        elif self.role in ['customer', 'delivery']:
            self.is_staff = False
            self.is_superuser = False
        
        self.is_active = self.active
            
        super().save(*args, **kwargs)
    
    @property
    def is_delivery(self):
        return self.role == 'delivery'