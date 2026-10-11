# Developed by AMIR AMMARZAD
from django.db import transaction
from django.db.models import F
from django.db.models.functions import Greatest
from django.utils import timezone

from . import shipping
from .models import Order, OrderItem, Product


@transaction.atomic
def create_order(cart, data):
    """سفارش را با اطلاعات لحظه‌ای قیمت می‌سازد (قیمت‌ها از دیتابیس خوانده می‌شوند، نه از کاربر)."""
    method = data["shipping_method"]
    s = cart.summary(method)
    order = Order.objects.create(
        name=data["name"], phone=data["phone"], province=data["province"], city=data["city"],
        address=data["address"], postal_code=data["postal_code"],
        shipping_method=method, shipping_cost=s["shipping_cost"],
        gift_wrap=cart.gift_wrap, wrap_cost=s["wrap_cost"], gift_note=cart.gift_note,
        subtotal=s["subtotal"], total=s["total"],
    )
    OrderItem.objects.bulk_create([
        OrderItem(order=order, product=l["product"], name=l["product"].name,
                  price=l["product"].price, qty=l["qty"])
        for l in s["lines"]
    ])
    return order


@transaction.atomic
def mark_paid(order_id, ref_id):
    """پس از تأیید بانک: وضعیت سفارش، موجودی و آمار فروش را اتمیک به‌روزرسانی می‌کند.
    اگر سفارش قبلاً پرداخت شده باشد (بازگشت دوباره از درگاه) کاری انجام نمی‌دهد."""
    order = Order.objects.select_for_update().get(pk=order_id)
    if order.status != Order.Status.PENDING:
        return order, False
    for item in order.items.all():
        if item.product_id:
            Product.objects.filter(pk=item.product_id).update(
                stock=Greatest(F("stock") - item.qty, 0),
                sold_count=F("sold_count") + item.qty,
            )
    order.status = Order.Status.PAID
    order.ref_id = ref_id
    order.paid_at = timezone.now()
    order.save(update_fields=["status", "ref_id", "paid_at"])
    return order, True
