from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from .views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('cellular.urls')),  
    path('', home, name='home'), 

    # --- بخش‌های مربوط به Swagger ---
    # 1. تولید فایل Schema (نقشه اصلی API)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # 2. رابط کاربری Swagger UI (همان محیط گرافیکی زیبا)
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # 3. رابط کاربری Redoc (یک نمای دیگر، اختیاری)
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]