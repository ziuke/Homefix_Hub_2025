from django.urls import path
from . import views

app_name = 'ratings'

urlpatterns = [
    path('review/create/<int:service_request_id>/', views.create_review, name='create_review'),
    path('review/edit/<int:review_id>/', views.edit_review, name='edit_review'),
    path('provider/<int:provider_id>/reviews/', views.provider_reviews, name='provider_reviews'),
    path('direct-request/<int:direct_request_id>/review/', views.direct_service_request_review, name='create_direct_service_request_review'),
    path('direct-request/<int:direct_request_id>/review/edit/', views.edit_direct_service_request_review, name='edit_direct_service_request_review'),
]
