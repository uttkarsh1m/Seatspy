# from django.urls import path
# from .views import HomePageView, CustomLoginView, SignUpView, CustomLogoutView, BroadcasterDashboardView, ViewerHomeView

# urlpatterns = [
#     path('', HomePageView.as_view(), name='home'),  # ✅ Home Page
#     path('login/', CustomLoginView.as_view(), name='login'),
#     path('signup/', SignUpView.as_view(), name='signup'),
#     path('logout/', CustomLogoutView.as_view(), name='logout'),
#     path('broadcaster/', BroadcasterDashboardView.as_view(), name='broadcaster_dashboard'),
#     path('viewer/', ViewerHomeView.as_view(), name='viewer_home'),
# ]


from django.urls import path
from .views import (
    HomePageView,
    CustomLoginView,
    SignUpView,
    CustomLogoutView,
    BroadcasterDashboardView,
    ViewerHomeView
)

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),  # Home Page
    path('login/', CustomLoginView.as_view(), name='login'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('broadcaster/', BroadcasterDashboardView.as_view(), name='broadcaster_dashboard'),
    path('viewer/', ViewerHomeView.as_view(), name='viewer_home'),
]

# Serve media files during development
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
