# Developed by AMIR AMMARZAD
"""
درگاه‌های پرداخت.

- MockGateway: درگاه آزمایشی داخلی برای توسعه و تست (بدون پول و اینترنت)
- ZarinpalGateway: زرین‌پال (API نسخه ۴)؛ با ZARINPAL_SANDBOX=1 در سندباکس کار می‌کند

برای افزودن درگاه دیگر (مثلاً بانکی)، یک کلاس با دو متد request و verify بنویسید
و در get_gateway() اضافه کنید.
"""
import secrets

import requests
from django.conf import settings
from django.urls import reverse


class GatewayError(Exception):
    """خطایی که پیام آن برای کاربر قابل نمایش است."""


class MockGateway:
    name = "mock"

    def request(self, request, order):
        authority = "MOCK" + secrets.token_hex(12).upper()
        return authority, reverse("shop:mock_bank", args=[authority])

    def verify(self, request, order):
        if request.GET.get("Status") != "OK":
            return False, ""
        return True, str(secrets.randbelow(9 * 10**11) + 10**11)


class ZarinpalGateway:
    name = "zarinpal"

    def __init__(self):
        host = "sandbox.zarinpal.com" if settings.ZARINPAL_SANDBOX else "payment.zarinpal.com"
        self.api = f"https://{host}/pg/v4/payment"
        self.start_url = f"https://{host}/pg/StartPay/"

    def _post(self, endpoint, payload):
        try:
            r = requests.post(f"{self.api}/{endpoint}.json", json=payload, timeout=20)
            data = r.json()
        except (requests.RequestException, ValueError):
            raise GatewayError("ارتباط با درگاه پرداخت برقرار نشد. چند دقیقه بعد دوباره تلاش کنید.")
        d = data.get("data")
        return d if isinstance(d, dict) else {}, data.get("errors")

    def request(self, request, order):
        payload = {
            "merchant_id": settings.ZARINPAL_MERCHANT_ID,
            "amount": order.total * 10,  # زرین‌پال مبلغ را به ریال می‌گیرد
            "callback_url": request.build_absolute_uri(reverse("shop:payment_callback")),
            "description": f"سفارش {order.code}",
            "metadata": {"mobile": order.phone},
        }
        d, errors = self._post("request", payload)
        if d.get("code") != 100 or not d.get("authority"):
            raise GatewayError("درگاه پرداخت درخواست را نپذیرفت. لطفاً دوباره تلاش کنید.")
        return d["authority"], self.start_url + d["authority"]

    def verify(self, request, order):
        if request.GET.get("Status") != "OK":
            return False, ""
        payload = {
            "merchant_id": settings.ZARINPAL_MERCHANT_ID,
            "amount": order.total * 10,
            "authority": order.authority,
        }
        d, errors = self._post("verify", payload)
        if d.get("code") in (100, 101):  # ۱۰۱ یعنی قبلاً تأیید شده
            return True, str(d.get("ref_id", ""))
        return False, ""


def get_gateway():
    if settings.PAYMENT_GATEWAY == "zarinpal":
        return ZarinpalGateway()
    return MockGateway()
