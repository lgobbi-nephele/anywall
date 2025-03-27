from django.urls import path
from.views import *
from django.contrib.auth.views import LogoutView
from django.contrib import admin
from django.views.generic.base import RedirectView

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
    path('api/latest-screenshot/', ScreenshotAPIView.as_view(), name='latest-screenshot'), #Added line
    path('upload/', upload_image, name='upload'),
    path('success/', success, name='success'),
    path('select-image/', select_image, name='select-image'),
    path('get-images-by-scope/', get_images_by_scope, name='get_images_by_scope'),
    path('anywall', setting, name='setting'),
    path('clock-view', clock_view, name='clock-view'),
    path('sender', sender, name='sender'),
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

#    logger.info("Registered ChangeWindowAPIView"),


# Add this at the end of your urls.py file

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)