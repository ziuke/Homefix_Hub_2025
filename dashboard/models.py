from django.db import models
from users.models import CustomUser

# Create your models here.

class ApprovalLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    approved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='approvals_made')
    approved_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {'Approved' if self.user.is_approved else 'Pending'}"

class AdminNotification(models.Model):
    NOTIFICATION_TYPES = (
        ('new_user', 'New User Registration'),
        ('approval_needed', 'Approval Needed'),
        ('other', 'Other'),
    )
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    related_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
