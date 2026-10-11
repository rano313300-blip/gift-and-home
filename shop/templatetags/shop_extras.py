# Developed by AMIR AMMARZAD
from django import template

register = template.Library()
_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


@register.filter
def fa(value):
    """ارقام فارسی."""
    return str(value).translate(_FA)


@register.filter
def num(value):
    """عدد با جداکننده هزارگان و ارقام فارسی."""
    try:
        return f"{int(value):,}".replace(",", "٬").translate(_FA)
    except (TypeError, ValueError):
        return fa(value)


@register.filter
def toman(value):
    return f"{num(value)} تومان"


@register.filter
def stars(value):
    n = round(float(value))
    return "★" * n + "☆" * (5 - n)


@register.filter
def mul(a, b):
    return a * b
