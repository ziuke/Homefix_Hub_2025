from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('<int:chat_room_id>/messages/', views.get_messages, name='get_messages'),
    path('<int:chat_room_id>/send/', views.send_message, name='send_message'),
]
