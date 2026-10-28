# Mehmonxona — bron qilish tizimi

Django va SQLite asosidagi oddiy mehmonxona bron qilish tizimi.

## Talablar

- Python 3.12 yoki undan yangi
- Internet (sahifalar dizayni Tailwind CDN orqali yuklanadi)

## O‘rnatish

**1. Virtual muhit yaratish va faollashtirish**

Linux / macOS / WSL:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

> Ubuntu/Debian’da `ensurepip is not available` xatosi chiqsa, avval
> `sudo apt install python3-venv` buyrug‘ini bajaring.

**2. Kutubxonalarni o‘rnatish**

```bash
pip install -r requirements.txt
```

**3. Ma’lumotlar bazasini yaratish**

```bash
python manage.py migrate
```

**4. Boshlang‘ich ma’lumotlarni yuklash** (3 ta xona turi va 10 ta xona)

```bash
python manage.py seed
```

Buyruqni qayta ishga tushirish xavfsiz — takroriy yozuvlar yaratilmaydi.

**5. Administrator yaratish**

```bash
python manage.py createsuperuser
```

**6. Serverni ishga tushirish**

```bash
python manage.py runserver
```

Brauzerda oching: <http://127.0.0.1:8000/>

## Sahifalar

| Manzil | Tavsif |
| --- | --- |
| `/` | Bo‘sh xonalarni sana va mehmonlar soni bo‘yicha qidirish |
| `/book/<id>/` | Xonani bron qilish formasi |
| `/rooms/` | Barcha xonalar rasmlari bilan va bugungi holati (bo‘sh / band). Xodimga mehmon ismi ham ko‘rinadi |
| `/rooms/<id>/` | Xona sahifasi: rasmlar galereyasi, narx, bron qilish. Xodimga hozirgi va yaqin bronlar ko‘rinadi |
| `/login/` | Menejerlar uchun kirish sahifasi |
| `/panel/` | Menejer paneli: bugun keladigan / ketadigan mehmonlar, keyingi 7 kun, bo‘sh / band xonalar |
| `/panel/rooms/<id>/photos/` | Xona rasmlarini yuklash, o‘chirish, asosiy rasmni tanlash |
| `/bookings/` | Bronlar ro‘yxati, ism / telefon / xona bo‘yicha qidirish va bekor qilish (menejerlar uchun) |
| `/admin/` | Admin panel: xona turlari, narxlar, foydalanuvchilar (faqat admin) |

## Rollar

- **Admin** — `createsuperuser` bilan yaratiladi, `/admin/` ga kiradi. Menejer ko‘radigan hamma narsani ham ko‘radi.
- **Menejer** — `/admin/` ga kira olmaydi. `/login/` orqali kirib `/panel/` da ishlaydi: bronlarni ko‘radi va bekor qiladi, xonalar rasmlarini boshqaradi, xonadagi mehmon ma’lumotlarini ko‘radi.
- **Mehmon** — kirishsiz xonalarni qidiradi va bron qiladi.

Menejer hisobini yaratish:

```bash
python manage.py create_manager menejer1
```

(parol so‘raladi). Yoki `/admin/` da foydalanuvchi yaratib, uni **Menejer** guruhiga qo‘shing
va “Staff status” belgisini qo‘ymang.

## Xona rasmlari

Menejer: `/panel/` → **Xonalar va rasmlar** → xonani oching → **Rasmlarni boshqarish**.
Bir vaqtda 10 tagacha rasm yuklash mumkin (JPG/PNG/WebP, har biri 5 MB gacha).
Birinchi rasm asosiy bo‘ladi, boshqasini “Asosiy qilish” tugmasi bilan almashtirish mumkin.
Admin buni `/admin/` → **Xonalar** orqali ham qila oladi. Rasmlar `media/` papkasida saqlanadi
(git’ga qo‘shilmaydi).

## Render.com ga joylash

Django loyihasi repo ichidagi `mexmoxona1/` papkasida. **Root Directory ni bo‘sh qoldiring**
(repo ildizi): ildizdagi `build.sh` o‘zi `mexmoxona1/` ga o‘tadi.

| Sozlama | Qiymat |
| --- | --- |
| Root Directory | *(bo‘sh)* |
| Build Command | `./build.sh` |
| Start Command | `cd mexmoxona1 && gunicorn hotel.wsgi` |

Environment o‘zgaruvchilari:

| Nomi | Qiymati |
| --- | --- |
| `DJANGO_DEBUG` | `0` |
| `DJANGO_SECRET_KEY` | uzun tasodifiy kalit (`python -c "import secrets;print(secrets.token_urlsafe(50))"`) |
| `DATABASE_URL` | Render PostgreSQL’ning *Internal Database URL* manzili |
| `DJANGO_SERVE_MEDIA` | `1` (rasmlarni Django o‘zi beradi) |
| `DJANGO_MEDIA_ROOT` | persistent disk yo‘li, masalan `/var/data/media` |
| `DJANGO_SUPERUSER_USERNAME` | admin logini |
| `DJANGO_SUPERUSER_PASSWORD` | admin paroli (har deploy’da shu qiymatga o‘rnatiladi) |

`RENDER_EXTERNAL_HOSTNAME` ni Render o‘zi beradi, `ALLOWED_HOSTS` va CSRF avtomatik sozlanadi.
Boshqa domen ulasangiz, `DJANGO_ALLOWED_HOSTS=domen.uz` qo‘shing.

> **Muhim:** Render’ning bepul xizmatida fayl tizimi doimiy emas. SQLite baza va yuklangan
> rasmlar har deploy yoki qayta ishga tushishda o‘chib ketadi. Bronlar uchun `DATABASE_URL`
> (PostgreSQL) ishlating, rasmlar uchun esa pullik xizmatga Persistent Disk ulang yoki rasmlarni
> alohida saqlash xizmatiga (masalan, Cloudinary) o‘tkazing.

Admin hisobi `DJANGO_SUPERUSER_*` o‘zgaruvchilaridan har deploy’da avtomatik yaratiladi (Shell kerak emas). Parolni o‘zgartirish uchun o‘zgaruvchini yangilab, qayta deploy qiling. Parolni kodga yozmang: repo ommaviy.

## Boshqa serverda (Nginx)

`DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS=domen.uz` o‘rnating,
`python manage.py collectstatic` ni ishga tushiring va `media/` papkasini Nginx orqali
`/media/` manzilida taqdim eting.

## Testlar

```bash
python manage.py test booking
```
