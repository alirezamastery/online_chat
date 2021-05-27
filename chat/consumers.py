import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from rest_framework.renderers import JSONRenderer
from django.contrib.auth import get_user_model

from .models import Chat, ChatMessage
from .serializers import MessageSerializer


User = get_user_model()


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        print(f'in connect | self.channel_name: {self.channel_name} | user: {self.scope["user"]}')
        self.user = self.scope.get('user', None)
        print('user type:', type(self.scope['user']), self.user.username)

        if self.user:
            self.room_name = self.scope['url_route']['kwargs']['room_name']
            self.room_group_name = f'chat_{self.room_name}'
            self.user_obj = User.objects.filter(username=self.user).first()
            try:
                chat_owner = User.objects.filter(username=self.room_name).first()
                self.chat_obj = Chat.objects.get(user=chat_owner)
            except:
                self.chat_obj = Chat.objects.create(user=self.user)
            print('chat_obj', self.chat_obj)
            print(f'room_name: {self.room_name} | room_group_name:{self.room_group_name}')
            async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
            self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        # message = text_data_json['message']
        # username = text_data_json['username']
        command = text_data_json['command']
        print('text_data_json:', text_data_json)
        # async_to_sync(self.channel_layer.group_send)(
        #     self.room_group_name,
        #     {
        #         'type':     'chatroom_message',
        #         'message':  message,
        #         'username': username
        #     }
        # )
        if command == 'new_message':
            self.new_message(text_data_json)
        elif command == 'fetch_message':
            self.fetch_message(text_data_json)
        else:
            print('wrong command')

    def new_message(self, data):
        message = data['message']
        # author = data['username']
        msg_obj = ChatMessage.objects.create(
            message=message,
            author=self.user_obj,
            chat=self.chat_obj,
            from_user=True if self.user.username == self.room_name else False
        )
        print('msg_obj:', msg_obj)
        result = self.message_serializer(msg_obj)
        print('result:', result)
        self.send_to_chat_message(result)

    def send_to_chat_message(self, message):
        command = message.get('command', None)
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type':    'chat_message',
                'message': message,
                'command': 'img' if (command == 'img') else 'new_message',
            }
        )

    def fetch_message(self, data):
        """
        when client connects it sends a payload with command='fetch_message'
        then this method fetches previous messages for the given username
        """
        print('in fetch_message | data:', data)
        # username = data['username']
        qs = self.chat_obj.chatmessage_set.all()
        print('in fetch_message | qs:', qs)
        message_json = self.message_serializer(qs)
        print('in fetch_message | message_json:', message_json)
        content = {
            'message': message_json,
            'command': 'fetch_message'
        }
        self.chat_message(content)

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

    # this method sends message to websocket
    def chat_message(self, event):
        # message = event['message']
        # username = event['username']
        print('event:', event)
        self.send(text_data=json.dumps(event))
