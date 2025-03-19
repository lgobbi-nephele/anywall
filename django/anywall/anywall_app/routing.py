from django.urls import path, re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/signaling/(?P<room_name>\w+)/$', consumers.SignalingConsumer.as_asgi()),
]

# websocket_urlpatterns = [
#     re_path(r'ws/signaling/$', consumers.SignalingConsumer.as_asgi()),
# ]