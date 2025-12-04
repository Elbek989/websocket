from django.urls import path
from chat import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Login sahifa
    path('', views.login_view, name='login'),
    path('chat-list/', views.chat_list, name='chat_list'),

    # CHAT — bu yerda faqat INT bo‘lishi kerak (user ID)
    path('chat/<int:room_name>/', views.chat_room, name='chat'),

    # FAYL YUKLASH uchun yangi endpoint qo'shing
    path('upload-file/', views.upload_file, name='upload_file'),
]

# DEBUG mode da media fayllarini ko'rsatish uchun
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)