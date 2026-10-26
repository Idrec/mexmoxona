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
| `/rooms/` | Barcha xonalar va bugungi holati (bo‘sh / band) |
| `/bookings/` | Bronlar ro‘yxati va bekor qilish (faqat xodimlar uchun) |
| `/admin/` | Boshqaruv paneli |

`/bookings/` sahifasiga kirish uchun avval `/admin/` orqali xodim
(`is_staff`) hisobi bilan tizimga kiring. Shundan so‘ng menyuda “Bronlar”
bo‘limi paydo bo‘ladi.

## Testlar

```bash
python manage.py test booking
```
