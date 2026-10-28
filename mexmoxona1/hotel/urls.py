from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

admin.site.site_header = 'Mehmonxona boshqaruvi'
admin.site.site_title = 'Mehmonxona'
admin.site.index_title = 'Boshqaruv paneli'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('booking.urls')),
]

if settings.SERVE_MEDIA:
    urlpatterns += [
        re_path(
            rf'^{settings.MEDIA_URL.lstrip("/")}(?P<path>.*)$',
            serve,
            {'document_root': settings.MEDIA_ROOT},
        ),
    ]
