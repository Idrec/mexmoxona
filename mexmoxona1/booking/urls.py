from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = 'booking'

urlpatterns = [
    path('login/', views.ManagerLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('panel/', views.panel, name='panel'),
    path('panel/rooms/<int:room_id>/photos/', views.room_photos, name='room_photos'),
    path('panel/rooms/<int:room_id>/photos/<int:image_id>/delete/',
         views.room_photo_delete, name='room_photo_delete'),
    path('panel/rooms/<int:room_id>/photos/<int:image_id>/cover/',
         views.room_photo_cover, name='room_photo_cover'),
    path('', views.home, name='home'),
    path('book/<int:room_id>/', views.book, name='book'),
    path('booking/<int:pk>/', views.confirmation, name='confirmation'),
    path('rooms/', views.rooms, name='rooms'),
    path('rooms/<int:room_id>/', views.room_detail, name='room_detail'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/<int:pk>/cancel/', views.cancel, name='cancel'),
]
