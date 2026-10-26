from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Booking, Room, RoomType
from .services import get_available_rooms


def day(offset):
    """A date `offset` days from today (views reject past dates)."""
    return timezone.localdate() + timedelta(days=offset)


class OverlapTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.room_type = RoomType.objects.create(
            name='Standart', price_per_night=Decimal('100000'), capacity=2
        )
        cls.room = Room.objects.create(number='101', room_type=cls.room_type, floor=1)
        # Existing stay: nights of day 10, 11, 12; guest leaves on day 13
        cls.existing = Booking.objects.create(
            room=cls.room, guest_name='Ali', phone='+998901112233',
            check_in=day(10), check_out=day(13),
        )

    def assertBlocked(self, check_in, check_out):
        self.assertNotIn(self.room, get_available_rooms(check_in, check_out))
        new = Booking(room=self.room, guest_name='Vali', phone='+998902223344',
                      check_in=check_in, check_out=check_out)
        with self.assertRaises(ValidationError):
            new.full_clean()

    def assertAllowed(self, check_in, check_out):
        self.assertIn(self.room, get_available_rooms(check_in, check_out))
        Booking(room=self.room, guest_name='Vali', phone='+998902223344',
                check_in=check_in, check_out=check_out).full_clean()

    def test_same_dates_overlap(self):
        self.assertBlocked(day(10), day(13))

    def test_partial_overlap(self):
        self.assertBlocked(day(8), day(11))   # ends inside the existing stay
        self.assertBlocked(day(12), day(15))  # starts inside the existing stay
        self.assertBlocked(day(11), day(12))  # fully inside
        self.assertBlocked(day(5), day(20))   # fully covers it

    def test_back_to_back_dates_allowed(self):
        self.assertAllowed(day(13), day(15))  # check in on the day the guest leaves
        self.assertAllowed(day(7), day(10))   # check out on the day the guest arrives

    def test_cancelled_booking_ignored(self):
        self.existing.status = Booking.Status.CANCELLED
        self.existing.save()
        self.assertAllowed(day(10), day(13))

    def test_inactive_rooms_and_capacity_filtered(self):
        Room.objects.create(number='102', room_type=self.room_type, floor=1, is_active=False)
        self.assertEqual(
            [r.number for r in get_available_rooms(day(1), day(2))], ['101']
        )
        self.assertEqual(list(get_available_rooms(day(1), day(2), guests=3)), [])

    def test_check_out_must_be_after_check_in(self):
        with self.assertRaises(ValidationError):
            Booking(room=self.room, guest_name='Vali', phone='+998902223344',
                    check_in=day(20), check_out=day(20)).full_clean()


class BookViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        room_type = RoomType.objects.create(
            name='Lyuks', price_per_night=Decimal('600000'), capacity=3
        )
        cls.room = Room.objects.create(number='201', room_type=room_type, floor=2)

    def book_url(self, check_in, check_out):
        return (reverse('booking:book', args=[self.room.pk])
                + f'?check_in={check_in.isoformat()}&check_out={check_out.isoformat()}')

    def test_successful_booking_redirects_to_confirmation(self):
        response = self.client.post(
            self.book_url(day(1), day(4)),
            {'guest_name': 'Aziza Karimova', 'phone': '+998 90 123 45 67'},
        )
        booking = Booking.objects.get()
        self.assertRedirects(response, reverse('booking:confirmation', args=[booking.pk]))
        self.assertEqual(booking.phone, '+998901234567')
        self.assertEqual(booking.total_price, Decimal('1800000'))

        page = self.client.get(reverse('booking:confirmation', args=[booking.pk]))
        self.assertContains(page, 'Aziza Karimova')
        self.assertContains(page, '1 800 000 so‘m')

    def test_double_booking_rejected_on_submit(self):
        Booking.objects.create(room=self.room, guest_name='Birinchi', phone='+998901111111',
                               check_in=day(2), check_out=day(5))
        response = self.client.post(
            self.book_url(day(3), day(6)),
            {'guest_name': 'Ikkinchi', 'phone': '+998902222222'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bu xona tanlangan sanalarda band.')
        self.assertEqual(Booking.objects.count(), 1)

    def test_staff_can_cancel_booking(self):
        booking = Booking.objects.create(room=self.room, guest_name='Ali', phone='+998901111111',
                                         check_in=day(1), check_out=day(3))
        cancel_url = reverse('booking:cancel', args=[booking.pk])

        # Anonymous visitors are redirected to the admin login
        self.assertEqual(self.client.post(cancel_url).status_code, 302)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.ACTIVE)

        staff = User.objects.create_user('admin', password='x', is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(cancel_url).status_code, 405)
        self.assertContains(self.client.get(reverse('booking:booking_list')), 'Ali')

        response = self.client.post(cancel_url, {'status': 'active'})
        self.assertRedirects(response, reverse('booking:booking_list') + '?status=active')
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CANCELLED)
        # The room is free again for those dates
        self.assertIn(self.room, get_available_rooms(day(1), day(3)))

    def test_confirmation_hidden_from_other_visitors(self):
        booking = Booking.objects.create(room=self.room, guest_name='Ali', phone='+998901111111',
                                         check_in=day(1), check_out=day(2))
        response = self.client.get(reverse('booking:confirmation', args=[booking.pk]))
        self.assertEqual(response.status_code, 404)
