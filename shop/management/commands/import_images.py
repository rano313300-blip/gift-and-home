# Developed by AMIR AMMARZAD
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from shop.models import Product


class Command(BaseCommand):
    help = "عکس‌های پوشه media_import را به محصولات وصل می‌کند (نام فایل = شماره یا نام محصول)."

    def handle(self, *args, **opts):
        folder = Path(settings.BASE_DIR) / "media_import"
        done = 0
        for f in sorted(folder.glob("*")):
            if f.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
                continue
            product = (Product.objects.filter(pk=int(f.stem)).first() if f.stem.isdigit()
                       else Product.objects.filter(name=f.stem).first())
            if not product:
                self.stdout.write(self.style.WARNING(f"محصولی برای {f.name} پیدا نشد"))
                continue
            with f.open("rb") as fh:
                product.image.save(f.name, File(fh), save=True)
            done += 1
        self.stdout.write(self.style.SUCCESS(f"{done} تصویر متصل شد."))
