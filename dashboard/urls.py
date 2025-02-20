from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('pending-approvals/', views.pending_approvals, name='pending_approvals'),
    path('user/<int:user_id>/', views.user_details, name='user_details'),
    path('approve/<int:user_id>/', views.approve_user, name='approve_user'),
    path('reject/<int:user_id>/', views.reject_user, name='reject_user'),
    path('users/', views.user_management, name='user_management'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('notifications/', views.notifications, name='notifications'),
    path('approval-logs/', views.approval_logs, name='approval_logs'),
    
    # Service Management
    path('service-categories/', views.service_categories, name='service_categories'),
    path('service-categories/add/', views.add_category, name='add_category'),
    path('service-categories/<int:category_id>/update/', views.update_category, name='update_category'),
    path('service-categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    path('service-requests/', views.service_requests, name='service_requests'),
    path('service-requests/<int:request_id>/', views.request_details, name='request_details'),
    path('provider-performance/', views.provider_performance, name='provider_performance'),
    path('direct-service-requests/', 
         views.dashboard_service_requests, 
         name='direct_service_requests'),
    
    path('direct-service-requests/<int:pk>/', 
         views.direct_request_detail, 
         name='direct_request_detail'),
    
    path('direct-service-requests/<int:pk>/update/', 
         views.direct_request_update, 
         name='direct_request_update'),
    
    path('direct-service-requests/<int:pk>/delete/', 
         views.direct_request_delete, 
         name='direct_request_delete'),
]
