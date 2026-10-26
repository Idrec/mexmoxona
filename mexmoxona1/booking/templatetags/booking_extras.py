from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def som(value):
    """1800000 -> '1 800 000 so‘m'"""
    if value in (None, ''):
        return ''
    return f'{Decimal(value):,.0f}'.replace(',', ' ') + ' so‘m'
