from django.urls import path
from . import views
from chat import views as chat_views
app_name = 'chat'

urlpatterns = [
    path('', views.notification_center, name='notification_center'),
    path('<int:chat_room_id>/messages/', views.get_messages, name='get_messages'),
    path('<int:chat_room_id>/send/', views.send_message, name='send_message'),
]
