import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from .models import Chat
from asgiref.sync import sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()


        self.user = self.scope['user']
        self.username = self.user.username if self.user.is_authenticated else "Anonim"
        print(f"{self.username} roomga connect qildi: {self.room_name}")

        # Oldingi xabarlarni yuborish
        await self.send_previous_messages()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            user = self.user

            # --- Oddiy xabar ---
            if 'message' in data and 'type' not in data:
                message = data['message']

                # Xabarni saqlash
                chat = await self.save_message(user, message)

                # Barchaga yuborish
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'id': chat.id,
                        'username': self.username,
                        'message': message
                    }
                )

            # --- Fayl xabari ---
            elif data.get('type') == 'file_message':
                file_url = data.get('file_url')
                file_name = data.get('file_name')
                file_type = data.get('file_type')
                file_size = data.get('file_size')
                message = data.get('message', f"Sent a file: {file_name}")

                # Fayl haqida xabarni saqlash
                chat = await self.save_file_message(user, message, file_url, file_name, file_type, file_size)

                # Barchaga yuborish
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'file_message_event',
                        'id': chat.id,
                        'username': self.username,
                        'message': message,
                        'file_url': file_url,
                        'file_name': file_name,
                        'file_type': file_type,
                        'file_size': file_size
                    }
                )

            elif data.get('action') == 'delete_messages':
                message_ids = data.get('message_ids', [])

                # Validation
                if not isinstance(message_ids, list):
                    await self.send_error("message_ids list bo'lishi kerak")
                    return

                # Bazadan o'chirish
                deleted_ids = await self.delete_messages_from_db(message_ids, user)

                if deleted_ids:

                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'delete_messages_event',
                            'message_ids': deleted_ids
                        }
                    )
                else:
                    await self.send_error("Xabarlar topilmadi yoki sizda ruxsat yo'q")

        except Exception as e:
            print(f"Error in receive: {e}")
            await self.send_error(f"Server error: {str(e)}")

    # ========== DATABASE FUNCTIONS ==========

    @sync_to_async
    def save_message(self, user, message):
        """Oddiy xabarni bazaga saqlash"""
        chat = Chat(
            user=user if user.is_authenticated else None,
            message=message,
            room_name=self.room_name,
            deleted=False
        )
        chat.save()
        return chat

    @sync_to_async
    def save_file_message(self, user, message, file_url, file_name, file_type, file_size):

        file_data = {
            'file_url': file_url,
            'file_name': file_name,
            'file_type': file_type,
            'file_size': file_size
        }

        chat = Chat(
            user=user if user.is_authenticated else None,
            message=message,
            room_name=self.room_name,
            deleted=False,
            is_file=True,
            file_data=file_data
        )
        chat.save()
        return chat

    @sync_to_async
    def delete_messages_from_db(self, message_ids, user):
        deleted_ids = []

        for msg_id in message_ids:
            try:
                chat = Chat.objects.get(
                    id=msg_id,
                    room_name=self.room_name,
                    deleted=False
                )

                if user.is_staff or (chat.user and chat.user.id == user.id):
                    chat.deleted = True
                    chat.save()
                    deleted_ids.append(msg_id)

            except Chat.DoesNotExist:
                continue

        return deleted_ids

    @sync_to_async
    def get_previous_messages(self):
        messages = Chat.objects.filter(
            room_name=self.room_name,
            deleted=False
        ).order_by('timestamp')[:50]

        result = []
        for msg in messages:
            if msg.is_file and msg.file_data:
                # Fayl xabari
                result.append({
                    'type': 'file',
                    'id': msg.id,
                    'username': msg.user.username if msg.user else "Anonim",
                    'message': msg.message,
                    'file_url': msg.file_data.get('file_url'),
                    'file_name': msg.file_data.get('file_name'),
                    'file_type': msg.file_data.get('file_type'),
                    'file_size': msg.file_data.get('file_size')
                })
            else:

                result.append({
                    'id': msg.id,
                    'username': msg.user.username if msg.user else "Anonim",
                    'message': msg.message
                })
        return result

    async def chat_message(self, event):
        """Yangi xabar handler"""
        await self.send(text_data=json.dumps({
            'id': event['id'],
            'username': event['username'],
            'message': event['message']
        }))

    async def file_message_event(self, event):
        """Fayl xabari handler"""
        await self.send(text_data=json.dumps({
            'type': 'file',
            'id': event['id'],
            'username': event['username'],
            'message': event.get('message', ''),
            'file_url': event['file_url'],
            'file_name': event['file_name'],
            'file_type': event['file_type'],
            'file_size': event['file_size']
        }))

    async def delete_messages_event(self, event):
        """Xabarlarni o'chirish handler"""
        await self.send(text_data=json.dumps({
            'action': 'delete',
            'message_ids': event['message_ids']
        }))



    async def send_previous_messages(self):
        """Oldingi xabarlarni yuborish"""
        messages = await self.get_previous_messages()

        for msg in messages:
            await self.send(text_data=json.dumps(msg))

    async def send_error(self, error_message):
        """Xatolik xabarini yuborish"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'error': error_message
        }))
