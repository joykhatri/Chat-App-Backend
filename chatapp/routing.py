from django.urls import re_path
from chatapp.consumers import *

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<chat_id>\w+)/$", ChatConsumer.as_asgi()),
    re_path(r"ws/homescreen/$", HomeScreenConsumer.as_asgi())
]