from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),          # Django'ning tayyor boshqaruv paneli (biz vaqtincha shundan foydalanamiz)
    path('', include('accounts.urls')),        # kirish/chiqish, ro'yxatdan o'tkazish
    path('core/', include('core.urls')),       # kurslar, guruhlar, darslar
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
