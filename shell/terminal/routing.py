from django.urls import re_path
from .consumers import CommandAndStreamConsumer

websocket_urlpatterns = [
    re_path(r'api/command-stream/$', CommandAndStreamConsumer.as_asgi()),
]
