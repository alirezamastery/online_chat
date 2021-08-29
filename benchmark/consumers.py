import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

from .models import ChatMessage


class ChatConsumer(WebsocketConsumer):

    def connect(self):
        self.room_group_name = 'benchmark'
        print('connect')
        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        print('text_data_json:', text_data_json)
        self.new_message(text_data_json)

    def new_message(self, data):
        message = data['msg_body']
        msg_obj = ChatMessage.objects.create(message=message)
        self.send_to_chat_message(str(msg_obj))

    def send_to_chat_message(self, message):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type':    'chat_message',
                'message': message,
            }
        )

    def chat_message(self, event):
        """this method sends message to websocket"""
        print(f'event: {event}')
        self.send(text_data=json.dumps(event))
