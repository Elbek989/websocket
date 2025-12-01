from django.urls import path
from chat import views
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),

    # Login sahifa
    path('', views.login_view, name='login'),
    path('chat-list/', views.chat_list, name='chat_list'),

    # CHAT — bu yerda faqat INT bo‘lishi kerak (user ID)
    path('chat/<int:room_name>/', views.chat_room, name='chat'),
]
