from django.urls import path

from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.home, name='home'),
    path('book/<int:room_id>/', views.book, name='book'),
    path('booking/<int:pk>/', views.confirmation, name='confirmation'),
    path('rooms/', views.rooms, name='rooms'),
    path('rooms/<int:room_id>/', views.room_detail, name='room_detail'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/<int:pk>/cancel/', views.cancel, name='cancel'),
]
