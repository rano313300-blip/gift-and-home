# Developed by AMIR AMMARZAD
"""روش‌های ارسال و محاسبه هزینه (تومان)."""
import math
from decimal import Decimal

FREE_SHIPPING_FROM = 3_000_000   # ارسال رایگان با پست عادی
GIFT_WRAP_COST = 45_000

METHODS = {
    "post": {
        "name": "پست عادی", "emoji": "📮", "base": 45_000, "extra": 10_000,
        "eta": "۵ تا ۹ روز کاری", "note": "اقتصادی‌ترین روش",
    },
    "pishtaz": {
        "name": "پست پیشتاز", "emoji": "🚚", "base": 75_000, "extra": 15_000,
        "eta": "۲ تا ۴ روز کاری", "note": "همراه با کد رهگیری پستی",
    },
    "tipax": {
        "name": "تیپاکس", "emoji": "⚡", "base": 98_000, "extra": 20_000,
        "eta": "۱ تا ۳ روز کاری", "note": "سریع، تحویل درب منزل",
    },
}
CHOICES = [(k, v["name"]) for k, v in METHODS.items()]

PROVINCES = [
    "آذربایجان شرقی", "آذربایجان غربی", "اردبیل", "اصفهان", "البرز", "ایلام", "بوشهر", "تهران",
    "چهارمحال و بختیاری", "خراسان جنوبی", "خراسان رضوی", "خراسان شمالی", "خوزستان", "زنجان",
    "سمنان", "سیستان و بلوچستان", "فارس", "قزوین", "قم", "کردستان", "کرمان", "کرمانشاه",
    "کهگیلویه و بویراحمد", "گلستان", "گیلان", "لرستان", "مازندران", "مرکزی", "هرمزگان",
    "همدان", "یزد",
]
PROVINCE_CHOICES = [(p, p) for p in PROVINCES]


def shipping_cost(method, subtotal, weight_kg):
    """هزینه ارسال: هزینه پایه برای تا ۱ کیلو + مبلغ اضافه برای هر کیلوی بعدی."""
    m = METHODS[method]
    if method == "post" and subtotal >= FREE_SHIPPING_FROM:
        return 0
    extra_kg = max(0, math.ceil(Decimal(weight_kg)) - 1)
    return m["base"] + extra_kg * m["extra"]
