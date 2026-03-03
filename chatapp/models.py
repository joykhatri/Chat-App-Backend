from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    username = None
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True, default='example@gmail.com')
    password = models.CharField(max_length=150)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.name
    
class Chat(models.Model):
    type = models.CharField(max_length=15, choices=[
        ('personal', 'Personal'),
        ('group', 'Group')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} chat ({self.id})"

class Message(models.Model):
    chat_id = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    sender_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    receiver_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages", null=True, blank=True)
    message = models.TextField()
    type = models.CharField(max_length=25, choices=[
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('file', 'File')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

class Group(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name="group_admin")
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class ChatMember(models.Model):
    chat_id = models.ForeignKey(Chat, on_delete=models.CASCADE, null=True, blank=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name="members")

    class Meta:
        unique_together = ('chat_id', 'user_id')