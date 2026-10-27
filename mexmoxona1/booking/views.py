from datetime import timedelta
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import BookingForm, ManagerLoginForm, RoomPhotosForm, SearchForm, StayForm
from .models import Booking, Room, RoomImage
from .permissions import is_manager, manager_required
from .services import (
    RoomNotAvailable,
    add_room_images,
    cancel_booking,
    create_booking,
    get_available_rooms,
    get_current_bookings,
    get_rooms_with_status,
    is_room_available,
    set_cover_image,
)

SESSION_KEY = 'booking_ids'


def _stay_query(check_in, check_out, guests=None):
    params = {'check_in': check_in.isoformat(), 'check_out': check_out.isoformat()}
    if guests:
        params['guests'] = guests
    return urlencode(params)


def home(request):
    if 'check_in' in request.GET:
        form = SearchForm(request.GET)
    else:
        today = timezone.localdate()
        form = SearchForm(initial={
            'check_in': today, 'check_out': today + timedelta(days=1), 'guests': 1,
        })

    context = {'form': form}
    if form.is_bound and form.is_valid():
        check_in = form.cleaned_data['check_in']
        check_out = form.cleaned_data['check_out']
        guests = form.cleaned_data['guests']
        nights = (check_out - check_in).days

        rooms = list(get_available_rooms(check_in, check_out, guests))
        for room in rooms:
            room.stay_total = room.room_type.price_per_night * nights

        context.update(
            rooms=rooms,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            nights=nights,
            stay_query=_stay_query(check_in, check_out),
        )
    return render(request, 'booking/home.html', context)


def book(request, room_id):
    room = get_object_or_404(
        Room.objects.select_related('room_type').prefetch_related('images'),
        pk=room_id, is_active=True,
    )
    stay_form = StayForm(request.GET)
    context = {'room': room, 'stay_form': stay_form}

    if not stay_form.is_valid():
        return render(request, 'booking/book.html', context)

    check_in = stay_form.cleaned_data['check_in']
    check_out = stay_form.cleaned_data['check_out']
    nights = (check_out - check_in).days
    available = is_room_available(room, check_in, check_out)

    form = BookingForm(request.POST or None)
    if request.method == 'POST' and available and form.is_valid():
        try:
            booking = create_booking(room, check_in, check_out, **form.cleaned_data)
        except RoomNotAvailable:
            available = False
        else:
            request.session[SESSION_KEY] = request.session.get(SESSION_KEY, []) + [booking.pk]
            return redirect('booking:confirmation', pk=booking.pk)

    context.update(
        form=form,
        available=available,
        check_in=check_in,
        check_out=check_out,
        nights=nights,
        total=room.room_type.price_per_night * nights,
        search_query=_stay_query(check_in, check_out, request.GET.get('guests')),
    )
    return render(request, 'booking/book.html', context)


def confirmation(request, pk):
    # Only the visitor who made the booking can see guest details
    if pk not in request.session.get(SESSION_KEY, []):
        raise Http404
    booking = get_object_or_404(Booking.objects.select_related('room__room_type'), pk=pk)
    return render(request, 'booking/confirmation.html', {'booking': booking})


def rooms(request):
    today = timezone.localdate()
    room_list = list(get_rooms_with_status(today))
    if is_manager(request.user):
        # Managers see who is staying in each busy room
        current = get_current_bookings(today)
        for room in room_list:
            room.current_booking = current.get(room.pk)
    context = {
        'today': today,
        'rooms': room_list,
        'free_count': sum(1 for r in room_list if r.is_active and not r.is_busy),
        'busy_count': sum(1 for r in room_list if r.is_active and r.is_busy),
    }
    return render(request, 'booking/rooms.html', context)


def room_detail(request, room_id):
    today = timezone.localdate()
    room = get_object_or_404(
        Room.objects.select_related('room_type').prefetch_related('images'), pk=room_id
    )
    if not room.is_active and not is_manager(request.user):
        raise Http404

    context = {
        'room': room,
        'images': list(room.images.all()),
        'is_busy': not is_room_available(room, today, today + timedelta(days=1)),
        'today': today,
        'stay_form': StayForm(initial={
            'check_in': today, 'check_out': today + timedelta(days=1),
        }),
    }
    if is_manager(request.user):
        context['current_booking'] = get_current_bookings(today).get(room.pk)
        context['upcoming'] = (
            room.bookings.active().filter(check_out__gt=today).order_by('check_in')[:5]
        )
    return render(request, 'booking/room_detail.html', context)


STATUS_FILTERS = [
    ('active', 'Faol'),
    ('cancelled', 'Bekor qilingan'),
    ('all', 'Hammasi'),
]


@manager_required
def booking_list(request):
    status = request.GET.get('status', 'active')
    if status not in dict(STATUS_FILTERS):
        status = 'active'

    query = request.GET.get('q', '').strip()

    bookings = Booking.objects.select_related('room__room_type').order_by('check_in', 'pk')
    if status != 'all':
        bookings = bookings.filter(status=status)
    if query:
        bookings = bookings.filter(
            Q(guest_name__icontains=query) | Q(phone__icontains=query) | Q(room__number__icontains=query)
        )

    return render(request, 'booking/booking_list.html', {
        'bookings': bookings,
        'status': status,
        'status_filters': STATUS_FILTERS,
        'query': query,
    })


@manager_required
@require_POST
def cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if cancel_booking(booking.pk):
        messages.success(request, f'Bron № {booking.pk} ({booking.guest_name}) bekor qilindi.')
    else:
        messages.error(request, f'Bron № {booking.pk} allaqachon bekor qilingan.')
    status = request.POST.get('status')
    if status not in dict(STATUS_FILTERS):
        status = 'active'
    params = {'status': status}
    if request.POST.get('q'):
        params['q'] = request.POST['q']
    return redirect(f"{reverse('booking:booking_list')}?{urlencode(params)}")


class ManagerLoginView(LoginView):
    template_name = 'booking/login.html'
    authentication_form = ManagerLoginForm
    redirect_authenticated_user = True


@manager_required
def panel(request):
    today = timezone.localdate()
    active = Booking.objects.active().select_related('room__room_type')
    room_list = list(get_rooms_with_status(today))
    active_rooms = [r for r in room_list if r.is_active]
    context = {
        'today': today,
        'arrivals': active.filter(check_in=today).order_by('room__number'),
        'departures': active.filter(check_out=today).order_by('room__number'),
        'upcoming': active.filter(
            check_in__gt=today, check_in__lte=today + timedelta(days=7)
        ).order_by('check_in', 'room__number'),
        'busy_count': sum(1 for r in active_rooms if r.is_busy),
        'free_count': sum(1 for r in active_rooms if not r.is_busy),
    }
    return render(request, 'booking/panel.html', context)


@manager_required
def room_photos(request, room_id):
    room = get_object_or_404(
        Room.objects.select_related('room_type').prefetch_related('images'), pk=room_id
    )
    if request.method == 'POST':
        form = RoomPhotosForm(request.POST, request.FILES)
        if form.is_valid():
            saved = add_room_images(room, form.cleaned_data['images'])
            messages.success(request, f'{len(saved)} ta rasm yuklandi.')
            return redirect('booking:room_photos', room_id=room.pk)
    else:
        form = RoomPhotosForm()
    return render(request, 'booking/room_photos.html', {
        'room': room, 'images': list(room.images.all()), 'form': form,
    })


@manager_required
@require_POST
def room_photo_delete(request, room_id, image_id):
    image = get_object_or_404(RoomImage, pk=image_id, room_id=room_id)
    image.delete()
    messages.success(request, 'Rasm o‘chirildi.')
    return redirect('booking:room_photos', room_id=room_id)


@manager_required
@require_POST
def room_photo_cover(request, room_id, image_id):
    image = get_object_or_404(RoomImage, pk=image_id, room_id=room_id)
    set_cover_image(image)
    messages.success(request, 'Asosiy rasm o‘zgartirildi.')
    return redirect('booking:room_photos', room_id=room_id)
