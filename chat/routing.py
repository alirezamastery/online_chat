from django.urls import re_path

from . import consumers, consumers_async

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers_async.ChatConsumer.as_asgi()),
]