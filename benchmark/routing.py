from django.urls import re_path

from . import consumers, consumers_async

websocket_urlpatterns = [
    re_path(r'ws/benchmark_sync/', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/benchmark_async/', consumers_async.AsyncChatConsumer.as_asgi()),
]