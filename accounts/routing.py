from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r"ws/support/(?P<session_id>[a-zA-Z0-9_-]+)/$",
        consumers.SupportConsumer.as_asgi(),
    ),
]