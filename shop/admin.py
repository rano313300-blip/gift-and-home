# Developed by AMIR AMMARZAD
from django.contrib import admin, messages

from .models import Category, ContactMessage, Order, OrderItem, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order")
    list_editable = ("order",)
    prepopulated_fields = {}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "old_price", "stock", "sold_count", "is_active")
    list_editable = ("price", "stock", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name", "description")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ("product", "name", "price", "qty")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "phone", "total", "status", "shipping_method", "tracking_code", "paid_at", "created_at")
    list_filter = ("status", "shipping_method", "payment_gateway", "province")
    search_fields = ("code", "name", "phone", "ref_id", "tracking_code")
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]
    readonly_fields = (
        "code", "subtotal", "shipping_cost", "wrap_cost", "total", "payment_gateway",
        "authority", "ref_id", "paid_at", "created_at",
    )
    fieldsets = (
        ("سفارش", {"fields": ("code", "status", "created_at", "paid_at")}),
        ("گیرنده", {"fields": ("name", "phone", "province", "city", "address", "postal_code")}),
        ("ارسال", {"fields": ("shipping_method", "shipping_cost", "tracking_code", "gift_wrap", "wrap_cost", "gift_note")}),
        ("پرداخت", {"fields": ("subtotal", "total", "payment_gateway", "authority", "ref_id")}),
        ("یادداشت", {"fields": ("admin_note",)}),
    )
    actions = ["mark_processing", "mark_shipped", "mark_delivered"]

    def _set(self, request, queryset, status, label):
        n = queryset.filter(paid_at__isnull=False).update(status=status)
        self.message_user(request, f"{n} سفارش به «{label}» تغییر کرد (فقط سفارش‌های پرداخت‌شده).", messages.SUCCESS)

    @admin.action(description="تغییر وضعیت به: در حال آماده‌سازی")
    def mark_processing(self, request, queryset):
        self._set(request, queryset, Order.Status.PROCESSING, "در حال آماده‌سازی")

    @admin.action(description="تغییر وضعیت به: ارسال شده")
    def mark_shipped(self, request, queryset):
        self._set(request, queryset, Order.Status.SHIPPED, "ارسال شده")

    @admin.action(description="تغییر وضعیت به: تحویل داده شده")
    def mark_delivered(self, request, queryset):
        self._set(request, queryset, Order.Status.DELIVERED, "تحویل داده شده")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "created_at", "is_read")
    list_filter = ("is_read",)
    list_editable = ("is_read",)
