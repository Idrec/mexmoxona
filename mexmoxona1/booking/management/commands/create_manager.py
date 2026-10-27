from getpass import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from booking.permissions import ensure_manager_group


class Command(BaseCommand):
    help = 'Menejer hisobini yaratadi (admin panelga kira olmaydi, faqat /panel/ ga).'

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('--password', help='Parol (berilmasa, so‘raladi)')

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        if User.objects.filter(username=username).exists():
            raise CommandError(f'“{username}” nomli foydalanuvchi allaqachon bor.')

        password = options['password'] or getpass('Parol: ')
        try:
            validate_password(password)
        except ValidationError as error:
            raise CommandError(' '.join(error.messages))

        user = User.objects.create_user(username, password=password)  # is_staff stays False
        user.groups.add(ensure_manager_group())
        self.stdout.write(self.style.SUCCESS(f'Menejer “{username}” yaratildi. Kirish: /login/'))
