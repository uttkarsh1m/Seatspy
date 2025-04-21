import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'live_broadcast.settings')

from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import broadcast_app.urls 

application = ProtocolTypeRouter({
    "http": django_asgi_app,  
    "websocket": AuthMiddlewareStack(
        URLRouter(broadcast_app.urls.websocket_urlpatterns)
    ),
})
