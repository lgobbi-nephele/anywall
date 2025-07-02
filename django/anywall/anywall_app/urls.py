from django.urls import path
from.views import *
from django.contrib.auth.views import LogoutView
from django.contrib import admin
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from django.views.generic.base import RedirectView
import sys

# Check if running in PyInstaller bundle
def is_pyinstaller():
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

# Base URL patterns that work in all environments
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/change-stream/', ChangeStreamAPIView.as_view(), name='change-stream'),
    path('api/api/switch-mode/', SwitchAPIView.as_view(), name='switch-mode'),
    path('api/zoom/', ZoomAPIView.as_view(), name='zoom'),
    path('api/restart/', RestartAPIView.as_view(), name='restart'),
    path('api/reset/', ResetAPIView.as_view(), name='reset'),
    path('api/change-layout/', ChangeLayoutAPIView.as_view(), name='change-layout'),
    path('api/browser/', BrowserAPIView.as_view(), name='browser'),
    path('api/browser-window/', BrowserWindowAPIView.as_view(), name='browser-window'),
    path('api/screen-share-window/', ScreenShareWindowAPIView.as_view(), name='screen-share-window'),
    path('api/alarm/', AlarmAPIView.as_view(), name='alarm'),
    path('api/alarm/clear/', AlarmClearAPIView.as_view(), name='alarm/clear'),
    path('api/alarm/expired/', AlarmExpiredAPIView.as_view(), name='alarm/expired'),
    path('api/latest-screenshot/', ScreenshotAPIView.as_view(), name='latest-screenshot'),
    path('upload/', upload_image, name='upload'),
    path('success/', success, name='success'),
    path('select-image/', select_image, name='select-image'),
    path('get-images-by-scope/', get_images_by_scope, name='get_images_by_scope'),
    path('anywall', setting, name='setting'),
    path('clock-view', clock_view, name='clock-view'),
    path('receiver', receiver, name='receiver'),
    path('signaling/', signaling, name='signaling'),
    path('get_offer/', get_offer, name='get_offer'),
    path('get_candidates/', get_candidates, name='get_candidates'),
    path('login', CustomLoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('setting', RedirectView.as_view(url='/anywall'), name='setting-redirect'),
    path('settings', RedirectView.as_view(url='/anywall'), name='setting-redirect'),
    path('', RedirectView.as_view(url='/anywall'), name='setting-redirect'),
]

# Only add drf_spectacular URLs if not in PyInstaller environment and if available
if not is_pyinstaller():
    try:
        from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
        
        urlpatterns += [
            path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
            path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
            path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
        ]
        print("Added drf_spectacular URLs to anywall_app")
    except ImportError as e:
        print(f"drf_spectacular not available in anywall_app: {e}")
        pass
else:
    print("PyInstaller environment detected in anywall_app - skipping drf_spectacular URLs")

# Add media files handling for development
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)