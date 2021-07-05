import json
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework.renderers import JSONRenderer

from .models import Chat, ChatMessage, SomeData
from .serializers import MessageSerializer


User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print(f'in connect | self.channel_name: {self.channel_name} | user: {self.scope["user"]}')
        self.user = self.scope.get('user', None)

        if self.user:
            self.room_name = self.scope['url_route']['kwargs']['room_name']
            self.room_group_name = f'chat_{self.room_name}'
            # - Use database_sync_to_async like this:
            # I think the last method in ORM method chain should not be called inside the parentheses
            # the call should be on whatever database_sync_to_async returns. not () at the end
            # self.user_obj = await database_sync_to_async(User.objects.filter(username=self.user).first)()
            # - Or like this:
            self.user_obj = await self.get_user()
            print(f'self.user_obj: {self.user_obj}')
            # try:
            #     # chat_owner = await database_sync_to_async(User.objects.filter(username=self.room_name).first)()
            #     # self.chat_obj = await database_sync_to_async(Chat.objects.get)(user=chat_owner)
            #     # self.chat_obj = await database_sync_to_async(Chat.objects.first)()
            #     self.chat_obj = await self.get_chat()
            # except:
            #     # self.chat_obj = await database_sync_to_async(Chat.objects.create)(user=self.user)
            #     self.chat_obj = await self.create_chat()
            #     print('except')
            self.chat_obj = await self.get_chat()
            print('chat_obj', self.chat_obj)
            print(f'room_name: {self.room_name} | room_group_name:{self.room_group_name}')
            data = SomeData.objects.get(pk=1)
            data.num = data.num + 1
            data.save(update_fields=['num'])
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()

    @database_sync_to_async
    def get_user(self):
        return User.objects.filter(username=self.user).first()

    @database_sync_to_async
    def get_chat(self):
        return Chat.objects.first()

    @database_sync_to_async
    def create_chat(self):
        return Chat.objects.create(user=self.user)


    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        command = text_data_json['command']
        print('text_data_json:', text_data_json)
        if command == 'new_message':
            await self.new_message(text_data_json)
        elif command == 'fetch_message':
            await self.fetch_message(text_data_json)
        else:
            print('wrong command')

    async def new_message(self, data):
        message = data['message']
        msg_obj = await database_sync_to_async(ChatMessage.objects.create)(
            message=message,
            author=self.user_obj,
            chat=self.chat_obj,
            from_user=True if self.user.username == self.room_name else False
        )
        print('msg_obj:', msg_obj)
        result = self.message_serializer(msg_obj)
        print('result:', result)
        await self.send_to_chat_message(result)

    async def send_to_chat_message(self, message):
        command = message.get('command', None)
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type':    'chat_message',
                'message': message,
                'command': 'img' if (command == 'img') else 'new_message',
            }
        )

    async def fetch_message(self, data):
        """
        when client connects it sends a payload with command='fetch_message'
        then this method fetches previous messages for the given username
        """
        print('in fetch_message | data:', data)
        qs = self.chat_obj.chatmessage_set.all()
        print('in fetch_message | qs:', qs)
        message_json = self.message_serializer(qs)
        print('in fetch_message | message_json:', message_json)
        content = {
            'message': message_json,
            'command': 'fetch_message'
        }
        await self.chat_message(content)

    @staticmethod
    def message_serializer(qs):
        serialized = MessageSerializer(
            qs,
            many=True if (qs.__class__.__name__ == 'QuerySet') else False
        )
        print('serialized.data:', serialized.data)
        content = JSONRenderer().render(serialized.data)
        print('JSONRenderered:', content)
        return serialized.data
        # return content

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))
