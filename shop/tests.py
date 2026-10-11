# Developed by AMIR AMMARZAD
import math
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.urls import reverse

from . import shipping
from .models import Category, Order, Product

CUSTOMER = dict(
    name="علی رضایی", phone="09121234567", province="تهران", city="تهران",
    address="خیابان ولیعصر، پلاک ۱۲", postal_code="1234567890", shipping_method="pishtaz",
)


class ShippingTests(TestCase):
    def test_free_post_over_threshold(self):
        self.assertEqual(shipping.shipping_cost("post", shipping.FREE_SHIPPING_FROM, 2), 0)

    def test_other_methods_not_free(self):
        self.assertGreater(shipping.shipping_cost("tipax", 10_000_000, 1), 0)

    def test_weight_surcharge(self):
        m = shipping.METHODS["post"]
        self.assertEqual(shipping.shipping_cost("post", 100_000, 2.5), m["base"] + 2 * m["extra"])


class PurchaseFlowTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="آشپزخانه", slug="kitchen")
        self.p = Product.objects.create(category=cat, name="قابلمه", price=1_000_000, weight_kg=1, stock=5)

    def _checkout(self, **over):
        self.client.post(reverse("shop:cart_add", args=[self.p.pk]), {"qty": 2})
        return self.client.post(reverse("shop:checkout"), {**CUSTOMER, **over})

    def test_full_purchase_with_mock_gateway(self):
        r = self._checkout()
        order = Order.objects.get()
        expected = 2_000_000 + shipping.shipping_cost("pishtaz", 2_000_000, 2)
        self.assertEqual(order.total, expected)
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertRedirects(r, reverse("shop:mock_bank", args=[order.authority]), fetch_redirect_response=False)

        cb = reverse("shop:payment_callback")
        self.client.get(cb, {"Authority": order.authority, "Status": "OK"})
        order.refresh_from_db()
        self.p.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertTrue(order.ref_id)
        self.assertEqual(self.p.stock, 3)
        self.assertEqual(self.p.sold_count, 2)
        self.assertNotIn("cart", self.client.session)

        # بازگشت دوباره از درگاه نباید موجودی را دوباره کم کند
        self.client.get(cb, {"Authority": order.authority, "Status": "OK"})
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 3)

    def test_failed_payment_keeps_order_pending(self):
        self._checkout()
        order = Order.objects.get()
        self.client.get(reverse("shop:payment_callback"), {"Authority": order.authority, "Status": "NOK"})
        order.refresh_from_db()
        self.p.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(self.p.stock, 5)

    def test_invalid_phone_rejected(self):
        r = self._checkout(phone="123")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)

    def test_persian_digits_accepted(self):
        self._checkout(phone="۰۹۱۲۱۲۳۴۵۶۷", postal_code="۱۲۳۴۵۶۷۸۹۰")
        order = Order.objects.get()
        self.assertEqual(order.phone, "09121234567")
        self.assertEqual(order.postal_code, "1234567890")

    def test_out_of_stock_cannot_be_added(self):
        self.p.stock = 0
        self.p.save()
        self.client.post(reverse("shop:cart_add", args=[self.p.pk]), {"qty": 1})
        r = self.client.get(reverse("shop:checkout"))
        self.assertRedirects(r, reverse("shop:cart"))

    def test_order_lookup_requires_matching_phone(self):
        self._checkout()
        order = Order.objects.get()
        bad = self.client.post(reverse("shop:track"), {"code": order.code, "phone": "09000000000"})
        self.assertEqual(bad.status_code, 200)
        ok = self.client.post(reverse("shop:track"), {"code": order.code, "phone": "۰۹۱۲۱۲۳۴۵۶۷"})
        self.assertRedirects(ok, order.get_absolute_url(), fetch_redirect_response=False)

    def test_all_pages_render(self):
        for name in ("home", "product_list", "cart", "track", "about"):
            self.assertEqual(self.client.get(reverse(f"shop:{name}")).status_code, 200, name)
        self.assertEqual(self.client.get(self.p.get_absolute_url()).status_code, 200)


def _resp(data):
    m = Mock()
    m.json.return_value = data
    return m


@override_settings(PAYMENT_GATEWAY="zarinpal", ZARINPAL_MERCHANT_ID="x" * 36, ZARINPAL_SANDBOX=True)
class ZarinpalTests(TestCase):
    def test_request_and_verify_use_rial_and_sandbox(self):
        cat = Category.objects.create(name="هدیه", slug="gift")
        p = Product.objects.create(category=cat, name="شمع", price=300_000, weight_kg=0.5, stock=3)
        with patch("shop.payments.requests.post") as post:
            post.side_effect = [
                _resp({"data": {"code": 100, "authority": "A" * 36}, "errors": []}),
                _resp({"data": {"code": 100, "ref_id": 98765}, "errors": []}),
            ]
            self.client.post(reverse("shop:cart_add", args=[p.pk]), {"qty": 1})
            r = self.client.post(reverse("shop:checkout"), {**CUSTOMER, "shipping_method": "tipax"})
            order = Order.objects.get()
            self.assertEqual(r.status_code, 302)
            self.assertTrue(r["Location"].startswith("https://sandbox.zarinpal.com/pg/StartPay/"))
            first_payload = post.call_args_list[0].kwargs["json"]
            self.assertEqual(first_payload["amount"], order.total * 10)

            self.client.get(reverse("shop:payment_callback"), {"Authority": order.authority, "Status": "OK"})
            order.refresh_from_db()
            self.assertEqual(order.status, Order.Status.PAID)
            self.assertEqual(order.ref_id, "98765")
