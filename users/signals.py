from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, TenantProfile, ServiceProviderProfile

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 'tenant':
            TenantProfile.objects.create(user=instance)
        elif instance.user_type == 'serviceprovider':
            ServiceProviderProfile.objects.create(user=instance)
