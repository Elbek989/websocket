from django.contrib.auth import authenticate,login,logout
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import  redirect,render


from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.is_superuser:
                return redirect("chat_list")

            return redirect("chat", room_name=user.id)

        return render(request, "login.html", {"error": "Xato login yoki parol!"})

    return render(request, "login.html")

@login_required
def chat_view(request, room_name):
    return render(request, 'chat.html', {
        'room_name': room_name,
        'username': request.user.username
    })
@login_required
def chat_room(request, room_name):
    return render(request, 'chat_room.html', {'room_name': room_name})

# Create your views here.
from django.shortcuts import redirect

def home(request):
    if request.user.is_authenticated:
        return redirect(f'/{request.user.id}/')
    return redirect('/login/')
from .models import Chat

def chat_list(request):
    users = User.objects.filter(is_superuser=False)
    return render(request, "chatlist.html", {"users": users})
from channels.db import database_sync_to_async

# Helper function to save chat

@database_sync_to_async
def save_message(user, room_name, message):
    # user: User instance bo'lishi kerak
    return Chat.objects.create(user=user, room_name=room_name, message=message)

@database_sync_to_async
def get_last_messages(room_name, limit=50):
    # oxirgi `limit` ta xabarni olish
    messages = Chat.objects.filter(room_name=room_name).order_by('-timestamp')[:limit]
    result = []
    for msg in messages:
        result.append({
            'message': msg.message,
            'username': msg.user.username
        })
    return result
def delete_message(user, room_name, message):
    return Chat.objects.filter(user=user, room_name=room_name).delete()