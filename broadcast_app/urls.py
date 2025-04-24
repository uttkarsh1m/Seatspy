from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views, consumers

urlpatterns = [
    path('', views.home_page_view, name='home'),
    path('login/', views.custom_login_view, name='login'),
    path('signup/', views.sign_up_view, name='signup'),
    path('logout/', views.custom_logout_view, name='logout'),
    path('viewer/dashboard/', views.viewer_dashboard_view, name='viewer_dashboard'),
    path('broadcaster/dashboard', views.broadcaster_dashboard_view, name='broadcaster_dashboard'),
    path('viewer/<int:roomId>/', views.viewer_room_view, name='viewer_room'),
    path('broadcaster/<int:roomId>/', views.broadcaster_room_view, name='broadcaster_room'),
]

websocket_urlpatterns = [
    re_path(r'^ws/broadcast/(?P<roomId>\w+)/$', consumers.FrameBroadcastConsumer.as_asgi()),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
