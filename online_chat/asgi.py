"""
ASGI config for online_chat project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from chat.routing import websocket_urlpatterns as chat_routes
from benchmark.routing import websocket_urlpatterns as benchmark_routes


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'online_chat.settings')

routes = chat_routes + benchmark_routes

application = ProtocolTypeRouter({
    "http":      get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routes
        )
    ),
})
