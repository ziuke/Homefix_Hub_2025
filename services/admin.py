from django.contrib import admin
from .models import (
    ServiceCategory, ServiceRequest, ServiceOffer,
    ServiceReview, ServiceMessage, ProviderProfile
)

# Register your models here.

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'tenant', 'category', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'category')
    search_fields = ('title', 'description', 'tenant__username', 'provider__username')
    date_hierarchy = 'created_at'

@admin.register(ServiceOffer)
class ServiceOfferAdmin(admin.ModelAdmin):
    list_display = ('service_request', 'provider', 'proposed_cost', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('service_request__title', 'provider__username')
    date_hierarchy = 'created_at'

@admin.register(ServiceReview)
class ServiceReviewAdmin(admin.ModelAdmin):
    list_display = ('service_request', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('service_request__title', 'comment')
    date_hierarchy = 'created_at'

@admin.register(ServiceMessage)
class ServiceMessageAdmin(admin.ModelAdmin):
    list_display = ('service_request', 'sender', 'created_at', 'is_read')
    list_filter = ('is_read',)
    search_fields = ('service_request__title', 'sender__username', 'message')
    date_hierarchy = 'created_at'

@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'total_reviews', 'is_available')
    list_filter = ('is_available', 'categories')
    search_fields = ('user__username', 'user__email')
    filter_horizontal = ('categories',)
