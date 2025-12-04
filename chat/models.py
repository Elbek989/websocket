from django.db import models
from django.contrib.auth.models import User
import json

class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    room_name = models.CharField(max_length=100)
    is_file = models.BooleanField(default=False)
    file_data = models.JSONField(null=True, blank=True)  # Fayl ma'lumotlari uchun JSON
    deleted = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.user.username if self.user else 'Anonim'}: {self.message[:50]}"