from django.db import models
from django.utils import timezone
from users.models import CustomUser
from services.models import ServiceRequest
from django.contrib.auth import get_user_model
# Create your models here.

class ChatRoom(models.Model):
    participants = models.ManyToManyField(get_user_model(), related_name='chat_rooms')
    service_request = models.OneToOneField(ServiceRequest, on_delete=models.CASCADE, related_name='chat_room')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chat for {self.service_request.title}"

    def get_participants(self):
        return [self.service_request.tenant, self.service_request.provider]

class Message(models.Model):
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.username} at {self.created_at}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save()




class Notification(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Notification for {self.user.username}: {self.message}'