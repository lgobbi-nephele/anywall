# from django.contrib import admin
from django.urls import path, include, re_path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from django.views.generic.base import RedirectView
import sys

# Check if running in PyInstaller bundle
def is_pyinstaller():
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

schema_view = get_schema_view(
    openapi.Info(
        title="AnyWall API",
        default_version='v2',
        description="API di comando per il display node",
    ),
    public=True,
    permission_classes=(AllowAny,),
)

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', include('anywall_app.urls')),
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
        print("Added drf_spectacular URLs")
    except ImportError as e:
        print(f"drf_spectacular not available: {e}")
        pass
else:
    print("PyInstaller environment detected - skipping drf_spectacular URLs")