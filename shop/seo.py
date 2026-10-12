from django.http import HttpResponse
from django.utils.xmlutils import escape

from .models import Product


def sitemap(request):
    """Generate a minimal sitemap using the active host and public product URLs."""
    urls = [
        request.build_absolute_uri("/"),
        request.build_absolute_uri("/shop/"),
        request.build_absolute_uri("/about/"),
    ]
    urls.extend(
        request.build_absolute_uri(product.get_absolute_url())
        for product in Product.objects.filter(is_active=True).order_by("pk")
    )
    body = '<?xml version="1.0" encoding="UTF-8"?>\n'
    body += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    body += "".join(f"  <url><loc>{escape(url)}</loc></url>\n" for url in urls)
    body += "</urlset>"
    return HttpResponse(body, content_type="application/xml; charset=utf-8")


def robots(request):
    sitemap_url = request.build_absolute_uri("/sitemap.xml")
    body = f"User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /cart/\nDisallow: /checkout/\nDisallow: /order/\nSitemap: {sitemap_url}\n"
    return HttpResponse(body, content_type="text/plain; charset=utf-8")
