import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'DJANGO_SUPERUSER_USERNAME va DJANGO_SUPERUSER_PASSWORD berilgan bo‘lsa, '
        'admin hisobini yaratadi yoki parolini yangilaydi. Har deploy’da xavfsiz ishlaydi.'
    )

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        if not (username and password):
            self.stdout.write('DJANGO_SUPERUSER_* o‘rnatilmagan, admin yaratilmadi.')
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': os.environ.get('DJANGO_SUPERUSER_EMAIL', '')},
        )
        user.is_staff = user.is_superuser = user.is_active = True
        user.set_password(password)  # same password as in the env var, so changing it there resets it
        user.save()
        self.stdout.write(self.style.SUCCESS(
            f'Admin “{username}” {"yaratildi" if created else "yangilandi"}.'
        ))
