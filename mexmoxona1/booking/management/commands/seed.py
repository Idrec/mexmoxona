from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from booking.models import Room, RoomType

ROOM_TYPES = [
    {
        'name': 'Standart',
        'price_per_night': Decimal('350000'),
        'capacity': 2,
        'description': 'Ikki kishilik oddiy xona, dush va Wi-Fi bilan.',
    },
    {
        'name': 'Lyuks',
        'price_per_night': Decimal('600000'),
        'capacity': 3,
        'description': 'Keng xona, mini-bar va shahar manzarasi.',
    },
    {
        'name': 'Oilaviy',
        'price_per_night': Decimal('800000'),
        'capacity': 5,
        'description': 'Oila uchun ikki xonali katta nomer.',
    },
]

# (room number, floor, room type name)
ROOMS = [
    ('101', 1, 'Standart'),
    ('102', 1, 'Standart'),
    ('103', 1, 'Standart'),
    ('104', 1, 'Standart'),
    ('201', 2, 'Lyuks'),
    ('202', 2, 'Lyuks'),
    ('203', 2, 'Lyuks'),
    ('301', 3, 'Oilaviy'),
    ('302', 3, 'Oilaviy'),
    ('303', 3, 'Oilaviy'),
]


class Command(BaseCommand):
    help = 'Boshlang‘ich ma’lumotlar: 3 ta xona turi va 10 ta xona yaratadi.'

    @transaction.atomic
    def handle(self, *args, **options):
        types = {}
        for data in ROOM_TYPES:
            room_type, _ = RoomType.objects.update_or_create(
                name=data['name'], defaults=data
            )
            types[room_type.name] = room_type

        created = 0
        for number, floor, type_name in ROOMS:
            _, is_new = Room.objects.update_or_create(
                number=number,
                defaults={'floor': floor, 'room_type': types[type_name], 'is_active': True},
            )
            created += is_new

        self.stdout.write(self.style.SUCCESS(
            f'Tayyor: {len(types)} ta xona turi, {len(ROOMS)} ta xona ({created} ta yangi).'
        ))
