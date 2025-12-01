# ChatConsumer.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .views import get_last_messages, save_message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        user = self.scope['user']
        if user.is_authenticated:
            print(f"{user.username} roomga connect qildi: {self.room_name}")
        else:
            print(f"Anonim foydalanuvchi roomga connect qildi: {self.room_name}")


        last_messages = await get_last_messages(self.room_name)
        for chat in reversed(last_messages):
            await self.send(text_data=json.dumps({
                'message': chat['message'],
                'username': chat['username'],
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        user = self.scope['user']


        username = user.username if user.is_authenticated else "Anonim"

        await save_message(user, self.room_name, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
            }
        )

    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        await self.send(text_data=json.dumps({
            'message': message,
            'username': username
        }))
