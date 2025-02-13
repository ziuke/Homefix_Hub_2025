from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('tenant', 'Tenant'),
        ('serviceprovider', 'Service Provider'),
        ('admin', 'Admin'),
    )
    
    user_type = models.CharField(max_length=15, choices=USER_TYPE_CHOICES)
    email = models.EmailField(unique=True)
    phone_regex = RegexValidator(
        regex=r'^[6-9]\d{9}$',
        message="Phone number must start with 6,7,8, or 9 and be exactly 10 digits long."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=10)
    is_email_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class TenantProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='tenant_profile')
    location = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.username}'s Tenant Profile"

class ServiceProviderProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='provider_profile')
    service_location = models.CharField(max_length=255)
    service_provided = models.CharField(max_length=255)
    certifications = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username}'s Service Provider Profile"
