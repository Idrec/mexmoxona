from django.db import transaction
from django.db.models import Exists, OuterRef

from .models import Booking, Room


class RoomNotAvailable(Exception):
    pass


def get_available_rooms(check_in, check_out, guests=1):
    """Active rooms that fit `guests` and have no active booking overlapping the stay."""
    busy_room_ids = Booking.objects.overlapping(check_in, check_out).values('room_id')
    return (
        Room.objects.filter(is_active=True, room_type__capacity__gte=guests)
        .exclude(pk__in=busy_room_ids)
        .select_related('room_type')
        .prefetch_related('images')
        .order_by('room_type__price_per_night', 'number')
    )


def is_room_available(room, check_in, check_out):
    return room.is_active and not (
        Booking.objects.overlapping(check_in, check_out).filter(room=room).exists()
    )


@transaction.atomic
def create_booking(room, check_in, check_out, guest_name, phone):
    """Re-check availability and create the booking inside one transaction."""
    room = Room.objects.select_for_update().select_related('room_type').get(pk=room.pk)
    if not is_room_available(room, check_in, check_out):
        raise RoomNotAvailable

    booking = Booking(
        room=room,
        guest_name=guest_name,
        phone=phone,
        check_in=check_in,
        check_out=check_out,
    )
    booking.full_clean()
    booking.save()
    return booking


def cancel_booking(booking_id):
    """Cancel an active booking. Returns False if it was already cancelled."""
    updated = Booking.objects.active().filter(pk=booking_id).update(
        status=Booking.Status.CANCELLED
    )
    return bool(updated)


def get_rooms_with_status(day):
    """All rooms, each annotated with `is_busy` for the given day."""
    busy_today = Booking.objects.active().filter(
        room=OuterRef('pk'), check_in__lte=day, check_out__gt=day
    )
    return (
        Room.objects.select_related('room_type')
        .prefetch_related('images')
        .annotate(is_busy=Exists(busy_today))
    )


def get_current_bookings(day):
    """Active bookings whose stay includes `day`, as {room_id: booking} (for staff)."""
    bookings = Booking.objects.active().filter(check_in__lte=day, check_out__gt=day)
    return {b.room_id: b for b in bookings}
