import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import broadcast_app.urls  

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'live_broadcast.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # Regular HTTP requests use Django’s built-in ASGI handler (for WSGI-like behavior)
    "websocket": AuthMiddlewareStack(  
        URLRouter(
            broadcast_app.urls.websocket_urlpatterns
        )
    ),
})
