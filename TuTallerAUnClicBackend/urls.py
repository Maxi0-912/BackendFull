from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenRefreshView


class TokenRefreshLimitadoView(TokenRefreshView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_refresh'


urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios/login/refresh/', TokenRefreshLimitadoView.as_view(), name='token_refresh'),
    path('', include('TuTallerApp.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
