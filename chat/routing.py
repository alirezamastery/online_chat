from django.urls import re_path

from . import consumers, consumers_async , consumers_aync_composition

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers_aync_composition.ChatConsumer.as_asgi()),
]