from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.templatetags.static import static
from django.urls import include, path
from django.views.generic import RedirectView

admin.site.site_header = "مدیریت فروشگاه دورهمی"
admin.site.site_title = "دورهمی"
admin.site.index_title = "پنل مدیریت | طراحی و توسعه: AMIR AMMARZAD"

urlpatterns = [
    path("favicon.ico", RedirectView.as_view(url=static("img/favicon.ico"), permanent=True)),
    path("admin/", admin.site.urls),
    path("", include("shop.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
