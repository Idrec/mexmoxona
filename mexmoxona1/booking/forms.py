import re

from django import forms
from django.utils import timezone

from .models import Booking

INPUT_CLASS = (
    'block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 '
    'shadow-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200'
)
ISO_DATE = '%Y-%m-%d'
REQUIRED = 'Bu maydonni to‘ldiring.'


def date_field(label):
    return forms.DateField(
        label=label,
        input_formats=[ISO_DATE],
        widget=forms.DateInput(format=ISO_DATE, attrs={'type': 'date', 'class': INPUT_CLASS}),
        error_messages={'required': REQUIRED, 'invalid': 'Sanani to‘g‘ri kiriting.'},
    )


class StayForm(forms.Form):
    check_in = date_field('Kelish sanasi')
    check_out = date_field('Ketish sanasi')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate().isoformat()
        for name in ('check_in', 'check_out'):
            self.fields[name].widget.attrs['min'] = today

    def clean(self):
        cleaned = super().clean()
        check_in, check_out = cleaned.get('check_in'), cleaned.get('check_out')
        if check_in and check_in < timezone.localdate():
            self.add_error('check_in', 'Kelish sanasi o‘tgan kun bo‘lishi mumkin emas.')
        if check_in and check_out and check_out <= check_in:
            self.add_error('check_out', 'Ketish sanasi kelish sanasidan keyin bo‘lishi kerak.')
        return cleaned


class SearchForm(StayForm):
    guests = forms.IntegerField(
        label='Mehmonlar soni',
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={'class': INPUT_CLASS}),
        error_messages={
            'required': REQUIRED,
            'invalid': 'Butun son kiriting.',
            'min_value': 'Kamida %(limit_value)s nafar mehmon bo‘lishi kerak.',
            'max_value': 'Ko‘pi bilan %(limit_value)s nafar mehmon.',
        },
    )


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['guest_name', 'phone']
        widgets = {
            'guest_name': forms.TextInput(attrs={
                'class': INPUT_CLASS, 'autocomplete': 'name', 'placeholder': 'Ism Familiya',
            }),
            'phone': forms.TextInput(attrs={
                'class': INPUT_CLASS, 'type': 'tel', 'autocomplete': 'tel',
                'placeholder': '+998 90 123 45 67',
            }),
        }
        error_messages = {
            'guest_name': {
                'required': REQUIRED,
                'max_length': 'Ko‘pi bilan %(limit_value)d ta belgi kiriting.',
            },
            'phone': {
                'required': REQUIRED,
                'max_length': 'Ko‘pi bilan %(limit_value)d ta belgi kiriting.',
            },
        }

    def clean_guest_name(self):
        name = self.cleaned_data['guest_name']
        if len(name) < 2:
            raise forms.ValidationError('Ismni to‘liq kiriting.')
        return name

    def clean_phone(self):
        phone = re.sub(r'[\s\-()]', '', self.cleaned_data['phone'])
        if not re.fullmatch(r'\+?\d{9,15}', phone):
            raise forms.ValidationError(
                'Telefon raqamini to‘g‘ri kiriting, masalan: +998 90 123 45 67.'
            )
        return phone
