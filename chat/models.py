from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    emoji = models.CharField(max_length=10, blank=True)
    preferences = models.TextField(blank=True)
    about = models.TextField(blank=True)
    is_online = models.BooleanField(default=False)
    last_activity = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.username}'s profile"

class ChatRoom(models.Model):
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    is_video_chat = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Chat between {', '.join(user.username for user in self.participants.all())}"

class Message(models.Model):
    TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
    ]
    
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)
    message_type = models.CharField(max_length=5, choices=TYPE_CHOICES, default='text')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"

class GuestUser(models.Model):
    name = models.CharField(max_length=100)
    session_key = models.CharField(max_length=100, unique=True)
    emoji = models.CharField(max_length=10, default='😊')
    preferences = models.TextField(blank=True)
    about = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_online = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Guest: {self.name}"
    
    class Meta:
        ordering = ['-last_activity']

    @classmethod
    def cleanup_old_users(cls):
        """Remove guest users that haven't been active for more than 24 hours"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_time = timezone.now() - timedelta(hours=24)
        cls.objects.filter(last_activity__lt=cutoff_time).delete()
