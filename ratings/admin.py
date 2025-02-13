from django.contrib import admin
from .models import ServiceReview

# Register your models here.

@admin.register(ServiceReview)
class ServiceReviewAdmin(admin.ModelAdmin):
    list_display = ['service_request', 'reviewer', 'provider', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['reviewer__username', 'provider__username', 'comment']
    date_hierarchy = 'created_at'
