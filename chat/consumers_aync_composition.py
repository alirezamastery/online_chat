import json
from django.contrib.auth import get_user_model
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework.renderers import JSONRenderer

from .models import Chat, ChatMessage, SomeData
from .serializers import MessageSerializer


User = get_user_model()


class CommandHandler:
    def __init__(self, user_obj, chat_obj, room_name):
        self.user_obj = user_obj
        self.chat_obj = chat_obj
        self.room_name = room_name
        self.code_map = {
            'new_message':   self.new_message,
            'fetch_message': self.fetch_message,
        }

    async def new_message(self, data):
        message = data['message']
        msg_obj = await database_sync_to_async(ChatMessage.objects.create)(
            message=message,
            author=self.user_obj,
            chat=self.chat_obj,
            from_user=True if self.user_obj.username == self.room_name else False
        )
        print('msg_obj:', msg_obj)
        result = await self.message_serializer(msg_obj)
        print('result:', result)
        return {
            'type':    'chat_message',
            'message': result,
            'command': 'new_message',
        }

    async def fetch_message(self, data):
        """
        when client connects it sends a payload with command='fetch_message'
        then this method fetches previous messages for the given username
        """
        print('in fetch_message | data:', data)
        # *** .all() is not executed immediately but only when it is consumed. so you should make it execute
        # inside database_sync_to_async !!!
        # qs = await database_sync_to_async(self.chat_obj.chatmessage_set.all)
        qs = await self.get_chat_messages()
        print(f'in fetch: qs type: {type(qs)} | {qs.__class__.__name__}')
        print('in fetch_message | qs:', qs)
        message_json = await self.message_serializer(qs)
        print('in fetch_message | message_json:', message_json)
        return {
            'type':    'chat_message',
            'message': message_json,
            'command': 'fetch_message'
        }

    @database_sync_to_async
    def get_chat_messages(self):
        return list(self.chat_obj.chatmessage_set.all().select_related('author', 'chat__user'))

    @staticmethod
    async def message_serializer(qs):
        serialized = MessageSerializer(
            qs,
            many=True if (type(qs) == list) else False  # or: many=True if (qs.__class__.__name__ == 'list') else False
        )
        print('serialized.data:', serialized.data)
        content = JSONRenderer().render(serialized.data)
        print('JSONRenderered:', content)
        return serialized.data
        # return content


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
            try:
                chat_owner = await database_sync_to_async(User.objects.filter(username=self.room_name).first)()
                self.chat_obj = await database_sync_to_async(Chat.objects.get)(user=chat_owner)
            except:
                self.chat_obj = await self.create_chat()
                print('in except')
            print('chat_obj', self.chat_obj)
            print(f'room_name: {self.room_name} | room_group_name:{self.room_group_name}')
            self.command_handler = CommandHandler(self.user, self.chat_obj, self.room_name)
            # somedata_objects = await database_sync_to_async(SomeData.objects.filter(id__gt=0).order_by)('id')
            somedata_objects = await self.get_somedata()
            print(f'some data objects: {somedata_objects}')
            data = await database_sync_to_async(SomeData.objects.get)(pk=1)
            data.num = data.num + 1
            await database_sync_to_async(data.save)(update_fields=['num'])
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()

    @database_sync_to_async
    def get_somedata(self):
        return list(SomeData.objects.filter(id__gt=0).order_by('id'))[:100]

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
        if command in self.command_handler.code_map:
            response = await self.command_handler.code_map[command](text_data_json)
        else:
            raise Exception('invalid command')
        await self.send_to_chat_message(response)

    async def send_to_chat_message(self, message):
        print(type(message))
        await self.channel_layer.group_send(
            self.room_group_name,
            message
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))
