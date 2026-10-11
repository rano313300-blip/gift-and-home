# Developed by AMIR AMMARZAD
import secrets

from django.db import models
from django.urls import reverse

from . import shipping


class Category(models.Model):
    name = models.CharField("نام", max_length=80)
    slug = models.SlugField("شناسه لاتین", unique=True, help_text="مثلاً kitchen")
    order = models.PositiveSmallIntegerField("ترتیب نمایش", default=0)

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ["order", "id"]

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, verbose_name="دسته", on_delete=models.PROTECT, related_name="products")
    name = models.CharField("نام محصول", max_length=200)
    description = models.TextField("توضیحات", blank=True)
    price = models.PositiveBigIntegerField("قیمت (تومان)")
    old_price = models.PositiveBigIntegerField("قیمت قبل از تخفیف", null=True, blank=True)
    image = models.ImageField("تصویر", upload_to="products/", blank=True)
    emoji = models.CharField("ایموجی (اگر تصویر ندارد)", max_length=8, default="🎁", blank=True)
    bg_color = models.CharField("رنگ پس‌زمینه", max_length=9, default="#e3f1ec", blank=True)
    weight_kg = models.DecimalField("وزن (کیلوگرم)", max_digits=6, decimal_places=2, default=1)
    stock = models.PositiveIntegerField("موجودی", default=0)
    sold_count = models.PositiveIntegerField("تعداد فروش", default=0)
    rating = models.DecimalField("امتیاز", max_digits=2, decimal_places=1, default=4.5)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ["-id"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("shop:product_detail", args=[self.pk])

    @property
    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return round((1 - self.price / self.old_price) * 100)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار پرداخت"
        PAID = "paid", "پرداخت‌شده"
        PROCESSING = "processing", "در حال آماده‌سازی"
        SHIPPED = "shipped", "ارسال شده"
        DELIVERED = "delivered", "تحویل داده شده"
        CANCELLED = "cancelled", "لغو شده"

    code = models.CharField("کد سفارش", max_length=20, unique=True, editable=False)
    status = models.CharField("وضعیت", max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)

    name = models.CharField("نام گیرنده", max_length=120)
    phone = models.CharField("موبایل", max_length=11)
    province = models.CharField("استان", max_length=40)
    city = models.CharField("شهر", max_length=80)
    address = models.TextField("نشانی")
    postal_code = models.CharField("کد پستی", max_length=10)

    shipping_method = models.CharField("روش ارسال", max_length=10, choices=shipping.CHOICES)
    shipping_cost = models.PositiveBigIntegerField("هزینه ارسال", default=0)
    gift_wrap = models.BooleanField("بسته‌بندی کادویی", default=False)
    wrap_cost = models.PositiveBigIntegerField("هزینه بسته‌بندی", default=0)
    gift_note = models.CharField("متن کارت پیام", max_length=200, blank=True)

    subtotal = models.PositiveBigIntegerField("جمع کالاها")
    total = models.PositiveBigIntegerField("مبلغ نهایی (تومان)")

    payment_gateway = models.CharField("درگاه", max_length=20, blank=True)
    authority = models.CharField("Authority", max_length=64, blank=True, db_index=True)
    ref_id = models.CharField("شماره پیگیری بانکی", max_length=40, blank=True)
    paid_at = models.DateTimeField("زمان پرداخت", null=True, blank=True)

    tracking_code = models.CharField("کد رهگیری مرسوله", max_length=40, blank=True)
    admin_note = models.TextField("یادداشت مدیر", blank=True)
    created_at = models.DateTimeField("زمان ثبت", auto_now_add=True)

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارش‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.code:
            while True:
                code = "DM-" + secrets.token_hex(5).upper()
                if not Order.objects.filter(code=code).exists():
                    self.code = code
                    break
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("shop:order_detail", args=[self.code])

    @property
    def shipping_info(self):
        return shipping.METHODS.get(self.shipping_method, {})

    @property
    def is_paid(self):
        return self.status not in (self.Status.PENDING, self.Status.CANCELLED)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField("نام محصول", max_length=200)
    price = models.PositiveBigIntegerField("قیمت واحد")
    qty = models.PositiveIntegerField("تعداد")

    class Meta:
        verbose_name = "آیتم سفارش"
        verbose_name_plural = "آیتم‌های سفارش"

    def __str__(self):
        return f"{self.name} × {self.qty}"

    @property
    def line_total(self):
        return self.price * self.qty


class ContactMessage(models.Model):
    name = models.CharField("نام", max_length=100)
    phone = models.CharField("موبایل", max_length=20, blank=True)
    text = models.TextField("پیام")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField("خوانده شد", default=False)

    class Meta:
        verbose_name = "پیام تماس"
        verbose_name_plural = "پیام‌های تماس"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name}: {self.text[:30]}"
