from django.urls import path
from . import views
from .views import direct_service_request_detail
from users.views import tenant_profile
app_name = 'services'

urlpatterns = [
    # Service Requests
    path('request/create/', views.service_request_create, name='request_create'),
    path('requests/', views.service_request_list, name='request_list'),
    path('request/<int:pk>/', views.service_request_detail, name='request_detail'),
    path('request/<int:pk>/offer/', views.submit_offer, name='submit_offer'),
    path('offer/<int:offer_id>/accept/', views.accept_offer, name='accept_offer'),
    path('request/<int:pk>/status/', views.update_request_status, name='update_status'),
    path('request/<int:pk>/review/', views.submit_review, name='submit_review'),
    path('request/<int:pk>/message/', views.send_message, name='send_message'),
    path('request/<int:service_request_id>/submit/', views.submit_offer_view, name='submit_offer_view'),
    
    # Provider Management
    path('providers/search/', views.search_providers, name='search_providers'),
    path('provider/<int:pk>/', views.provider_profile, name='provider_profile'),
    path('provider/dashboard/', views.provider_dashboard, name='provider_dashboard'),
     # Create a direct service request (tenant selects a provider)
    path('direct-request/create/<int:provider_id>/', 
         views.direct_service_request_create, 
         name='direct_service_request_create'),

    # List direct service requests (different view for tenant vs. provider)
    path('direct-request/', 
         views.direct_service_request_list, 
         name='direct_service_request_list'),

    # Update a direct service request (only provider can accept/reject)
    path('direct-request/<int:pk>/update/', 
         views.direct_service_request_update, 
         name='direct_service_request_update'),

    path('direct-request/<int:pk>/', views.direct_service_request_detail, name='direct_service_request_detail'),
    path('tenant-profile/<int:pk>/', views.tenant_profile, name='tenant_profile'),
    path('all-activities/', views.all_activites, name='all_activites'),

]
