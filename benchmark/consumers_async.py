import json

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async

from .models import ChatMessage


class AsyncChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_group_name = 'benchmark'
        print('connect')
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        print('text_data_json:', text_data_json)
        await self.new_message(text_data_json)

    async def new_message(self, data):
        message = data['msg_body']
        msg_obj = await self.create_chat(message)
        await self.send_to_chat_message(str(msg_obj))

    async def send_to_chat_message(self, message):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type':    'chat_message',
                'message': message,
            }
        )

    async def chat_message(self, event):
        """this method sends message to websocket"""
        print(f'event: {event}')
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def create_chat(self, msg):
        return ChatMessage.objects.create(message=msg)
