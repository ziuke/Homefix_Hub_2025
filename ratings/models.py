from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from services.models import ServiceRequest, DirectServiceRequest
from django.db import models

class ServiceReview(models.Model):
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='service_reviews'  # Changed from 'service_requests' to 'service_reviews'
    )
    service_request = models.OneToOneField(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name='review'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='given_service_reviews'  # Changed to avoid conflict
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

class DirectServiceRequestReview(models.Model):
    direct_request = models.OneToOneField(
        DirectServiceRequest,
        on_delete=models.CASCADE,
        related_name='review'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='given_direct_service_reviews'  # Changed to avoid conflict
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
        return f"Review for {self.direct_request.provider} by {self.reviewer}"
        
    @property
    def provider(self):
        return self.direct_request.provider