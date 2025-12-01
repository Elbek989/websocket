from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.db import models

class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # foydalanuvchi
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    room_name = models.CharField(max_length=50)
