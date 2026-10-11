# Developed by AMIR AMMARZAD
import re

from django import forms

from . import shipping

_FA = "۰۱۲۳۴۵۶۷۸۹"
_AR = "٠١٢٣٤٥٦٧٨٩"
_TABLE = {ord(c): str(i) for i, c in enumerate(_FA)} | {ord(c): str(i) for i, c in enumerate(_AR)}


def normalize_digits(s):
    return str(s).translate(_TABLE).strip()


class CheckoutForm(forms.Form):
    name = forms.CharField(label="نام و نام خانوادگی", min_length=3, max_length=120)
    phone = forms.CharField(label="شماره موبایل", max_length=15)
    province = forms.ChoiceField(label="استان", choices=[("", "انتخاب کنید")] + shipping.PROVINCE_CHOICES)
    city = forms.CharField(label="شهر", min_length=2, max_length=80)
    address = forms.CharField(label="نشانی کامل", min_length=8, widget=forms.Textarea(attrs={"rows": 2}))
    postal_code = forms.CharField(label="کد پستی ۱۰ رقمی", max_length=15)
    shipping_method = forms.ChoiceField(label="روش ارسال", choices=shipping.CHOICES, widget=forms.RadioSelect)

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_phone(self):
        v = normalize_digits(self.cleaned_data["phone"])
        if not re.fullmatch(r"09\d{9}", v):
            raise forms.ValidationError("شماره موبایل باید با ۰۹ شروع شود و ۱۱ رقم باشد.")
        return v

    def clean_postal_code(self):
        v = normalize_digits(self.cleaned_data["postal_code"])
        if not re.fullmatch(r"\d{10}", v):
            raise forms.ValidationError("کد پستی باید ۱۰ رقم باشد.")
        return v


class ContactForm(forms.Form):
    name = forms.CharField(min_length=2, max_length=100)
    phone = forms.CharField(required=False, max_length=20)
    text = forms.CharField(min_length=5, max_length=2000)


class TrackForm(forms.Form):
    code = forms.CharField(max_length=20)
    phone = forms.CharField(max_length=15)

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()

    def clean_phone(self):
        return normalize_digits(self.cleaned_data["phone"])
