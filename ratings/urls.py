from django.urls import path
from . import views

app_name = 'ratings'

urlpatterns = [
    path('review/create/<int:service_request_id>/', views.create_review, name='create_review'),
    path('review/edit/<int:review_id>/', views.edit_review, name='edit_review'),
    path('provider/<int:provider_id>/reviews/', views.provider_reviews, name='provider_reviews'),
]
