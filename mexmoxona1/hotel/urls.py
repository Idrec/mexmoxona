from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'Mehmonxona boshqaruvi'
admin.site.site_title = 'Mehmonxona'
admin.site.index_title = 'Boshqaruv paneli'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('booking.urls')),
]
