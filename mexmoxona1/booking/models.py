import uuid
from decimal import Decimal
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


class RoomType(models.Model):
    name = models.CharField('Nomi', max_length=100)
    price_per_night = models.DecimalField('Bir kecha narxi', max_digits=10, decimal_places=2)
    capacity = models.PositiveIntegerField('Sig‘imi (kishi)')
    description = models.TextField('Tavsif', blank=True)

    class Meta:
        verbose_name = 'Xona turi'
        verbose_name_plural = 'Xona turlari'
        ordering = ['price_per_night']

    def __str__(self):
        return self.name


class Room(models.Model):
    number = models.CharField('Xona raqami', max_length=10, unique=True)
    room_type = models.ForeignKey(
        RoomType, on_delete=models.PROTECT, related_name='rooms', verbose_name='Xona turi'
    )
    floor = models.PositiveIntegerField('Qavat')
    is_active = models.BooleanField('Faol', default=True)

    class Meta:
        verbose_name = 'Xona'
        verbose_name_plural = 'Xonalar'
        ordering = ['number']

    def __str__(self):
        return f'{self.number} ({self.room_type})'

    @property
    def cover_image(self):
        """First photo of the room, or None. Uses prefetched images when available."""
        images = list(self.images.all())
        return images[0] if images else None


def validate_image_size(file):
    if file.size > MAX_IMAGE_SIZE:
        raise ValidationError('Rasm hajmi 5 MB dan oshmasligi kerak.')


def room_image_path(instance, filename):
    # Random name: no clashes between uploads and no user-controlled file names on disk
    return f'rooms/{instance.room_id}/{uuid.uuid4().hex}{Path(filename).suffix.lower()}'


class RoomImage(models.Model):
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name='images', verbose_name='Xona'
    )
    image = models.ImageField('Rasm', upload_to=room_image_path, validators=[validate_image_size])
    caption = models.CharField('Izoh', max_length=150, blank=True)
    order = models.PositiveIntegerField('Tartib', default=0, help_text='Kichik raqam birinchi chiqadi')

    class Meta:
        verbose_name = 'Xona rasmi'
        verbose_name_plural = 'Xona rasmlari'
        ordering = ['order', 'pk']

    def __str__(self):
        return f'{self.room.number} — rasm {self.pk}'


@receiver(post_delete, sender=RoomImage)
def delete_image_file(sender, instance, **kwargs):
    """Remove the file from disk when its row is deleted."""
    if instance.image:
        instance.image.delete(save=False)


class BookingQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status=Booking.Status.ACTIVE)

    def overlapping(self, check_in, check_out):
        """Active bookings that intersect the [check_in, check_out) stay."""
        return self.active().filter(check_in__lt=check_out, check_out__gt=check_in)


class Booking(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Faol'
        CANCELLED = 'cancelled', 'Bekor qilingan'

    room = models.ForeignKey(
        Room, on_delete=models.PROTECT, related_name='bookings', verbose_name='Xona'
    )
    guest_name = models.CharField('Mehmon ismi', max_length=150)
    phone = models.CharField('Telefon', max_length=20)
    check_in = models.DateField('Kelish sanasi')
    check_out = models.DateField('Ketish sanasi')
    status = models.CharField('Holati', max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField('Yaratilgan vaqti', auto_now_add=True)

    objects = BookingQuerySet.as_manager()

    class Meta:
        verbose_name = 'Bron'
        verbose_name_plural = 'Bronlar'
        ordering = ['-check_in']

    def __str__(self):
        return f'{self.guest_name} — {self.room.number} ({self.check_in} – {self.check_out})'

    def clean(self):
        # Fields may be missing if they failed their own validation
        if not (self.check_in and self.check_out):
            return

        if self.check_out <= self.check_in:
            raise ValidationError(
                {'check_out': 'Ketish sanasi kelish sanasidan keyin bo‘lishi kerak.'}
            )

        if self.status != self.Status.ACTIVE or not self.room_id:
            return

        overlapping = (
            Booking.objects.overlapping(self.check_in, self.check_out)
            .filter(room_id=self.room_id)
            .exclude(pk=self.pk)
        )
        if overlapping.exists():
            raise ValidationError(
                'Bu xona tanlangan sanalarda band. Boshqa sana yoki xonani tanlang.'
            )

    @property
    def nights(self):
        if not (self.check_in and self.check_out):
            return 0
        return (self.check_out - self.check_in).days

    @property
    def total_price(self):
        if not self.room_id:
            return Decimal('0')
        return self.nights * self.room.room_type.price_per_night
