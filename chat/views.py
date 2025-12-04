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
    return Chat.objects.create(user=user, room_name=room_name, message=message)

@database_sync_to_async
def get_last_messages(room_name, limit=50):
    messages = Chat.objects.filter(room_name=room_name).order_by('-timestamp')[:limit]
    result = []
    for msg in messages:
        result.append({
            'message': msg.message,
            'username': msg.user.username
        })
    return result
@database_sync_to_async
def delete_messages(message_ids):
    """
    message_ids: list of Chat.id
    """
    return Chat.objects.filter(id__in=message_ids).delete()


from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.conf import settings
import os
from datetime import datetime
import uuid
import json


# ... boshqa mavjud funksiyalar ...

@csrf_exempt
@login_required
def upload_file(request):
    """
    Fayl yuklash uchun view funksiyasi
    """
    print("📥 upload_file funksiyasi chaqirildi")

    # Faqat POST metodiga ruxsat berish
    if request.method != 'POST':
        print("❌ Faqat POST metodiga ruxsat")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    # Fayl borligini tekshirish
    if 'file' not in request.FILES:
        print("❌ Fayl topilmadi")
        return JsonResponse({'error': 'No file provided'}, status=400)

    file = request.FILES['file']
    room_name = request.POST.get('room_name', 'default')
    user = request.user

    print(f"📄 Fayl: {file.name}, hajmi: {file.size} bytes, tipi: {file.content_type}")
    print(f"🏠 Room: {room_name}, User: {user.username}")

    # Fayl hajmini tekshirish (max 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    if file.size > MAX_FILE_SIZE:
        print(f"❌ Fayl hajmi katta: {file.size} > {MAX_FILE_SIZE}")
        return JsonResponse({'error': 'File size too large. Maximum 10MB'}, status=400)

    # Ruxsat berilgan fayl turlari
    ALLOWED_TYPES = [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
    ]

    if file.content_type not in ALLOWED_TYPES and not file.content_type.startswith('image/'):
        print(f"❌ Fayl turi ruxsat berilmagan: {file.content_type}")
        return JsonResponse({'error': 'File type not allowed'}, status=400)

    try:
        # Fayl nomini xavfsiz qilish
        original_name = file.name
        file_ext = os.path.splitext(original_name)[1]
        safe_filename = f"{uuid.uuid4().hex}{file_ext}"

        # Papka yaratish
        # MEDIA_ROOT = .../media/
        # upload_dir = uploads/chat_files/room_name/2024/12/03/
        upload_dir = os.path.join('uploads', 'chat_files', str(room_name), datetime.now().strftime('%Y/%m/%d'))
        full_dir = os.path.join(settings.MEDIA_ROOT, upload_dir)

        # Papka mavjud emas bo'lsa yaratish
        os.makedirs(full_dir, exist_ok=True)
        print(f"📂 Papka yaratildi: {full_dir}")

        # Faylni saqlash
        file_path = os.path.join(upload_dir, safe_filename)
        saved_path = default_storage.save(file_path, file)

        print(f"✅ Fayl saqlandi: {saved_path}")


        file_url = f"{settings.MEDIA_URL}{saved_path}"

        # DEBUG mode da to'liq URL yaratish
        if settings.DEBUG:
            file_url = request.build_absolute_uri(file_url)

        print(f"🔗 Fayl URL: {file_url}")

        return JsonResponse({
            'success': True,
            'file_url': file_url,
            'file_name': original_name,
            'file_type': file.content_type,
            'file_size': file.size
        })

    except Exception as e:
        print(f"❌ Xatolik yuz berdi: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)