from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, TenantProfile, ServiceProviderProfile

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_approved', 'is_email_verified')
    list_filter = ('user_type', 'is_approved', 'is_email_verified')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Status', {'fields': ('user_type', 'is_approved', 'is_email_verified')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type'),
        }),
    )
    search_fields = ('username', 'email', 'phone_number')
    ordering = ('username',)

class TenantProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location')
    search_fields = ('user__username', 'location')



class ServiceProviderProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'service_location', 'get_services')

    def get_services(self, obj):
        return ", ".join([service.name for service in obj.service_provided.all()])

    get_services.short_description = 'Services Provided'

admin.site.register(ServiceProviderProfile, ServiceProviderProfileAdmin)
