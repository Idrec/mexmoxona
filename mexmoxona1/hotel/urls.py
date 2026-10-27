from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'Mehmonxona boshqaruvi'
admin.site.site_title = 'Mehmonxona'
admin.site.index_title = 'Boshqaruv paneli'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('booking.urls')),
]

# Dev server only; returns [] when DEBUG is off
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
