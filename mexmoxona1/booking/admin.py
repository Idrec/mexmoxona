from django.contrib import admin

from .models import Booking, Room, RoomType


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_per_night', 'capacity')
    search_fields = ('name',)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('number', 'room_type', 'floor', 'is_active')
    list_filter = ('room_type', 'floor', 'is_active')
    search_fields = ('number',)
    list_select_related = ('room_type',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'guest_name', 'phone', 'room', 'check_in', 'check_out',
        'nights_display', 'total_price_display', 'status', 'created_at',
    )
    list_filter = ('status', 'room__room_type', 'check_in')
    search_fields = ('guest_name', 'phone')
    list_select_related = ('room__room_type',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'check_in'

    @admin.display(description='Kechalar')
    def nights_display(self, obj):
        return obj.nights

    @admin.display(description='Umumiy narx')
    def total_price_display(self, obj):
        return obj.total_price
