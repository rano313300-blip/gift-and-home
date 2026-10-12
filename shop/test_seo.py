from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


class SearchDiscoveryTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="هدیه", slug="gift")
        self.active = Product.objects.create(
            category=category, name="ماگ کادویی", price=250_000, stock=2, is_active=True
        )
        self.hidden = Product.objects.create(
            category=category, name="محصول مخفی", price=100_000, stock=1, is_active=False
        )

    def test_sitemap_includes_public_pages_and_active_products_only(self):
        response = self.client.get(reverse("shop:sitemap"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml; charset=utf-8")
        body = response.content.decode()
        self.assertIn(self.active.get_absolute_url(), body)
        self.assertNotIn(self.hidden.get_absolute_url(), body)
        self.assertIn("/shop/", body)
        self.assertIn("/about/", body)

    def test_robots_points_to_sitemap_and_disallows_private_flows(self):
        response = self.client.get(reverse("shop:robots"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn("Sitemap: http://testserver/sitemap.xml", body)
        self.assertIn("Disallow: /checkout/", body)
        self.assertIn("Disallow: /admin/", body)
