from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from services.models import ServiceRequest

# Create your models here.

class ServiceReview(models.Model):
    service_request = models.OneToOneField(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name='review'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='given_reviews'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Review for {self.service_request.provider} by {self.reviewer}"
        
    @property
    def provider(self):
        return self.service_request.provider
