# Developed by AMIR AMMARZAD
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import shipping
from .cart import Cart
from .forms import CheckoutForm, ContactForm, TrackForm
from .models import ContactMessage, Category, Order, Product
from .payments import GatewayError, get_gateway
from .services import create_order, mark_paid


# ---------- صفحات اصلی ----------
def home(request):
    products = Product.objects.filter(is_active=True, stock__gt=0)
    return render(request, "shop/home.html", {
        "best": products.order_by("-sold_count", "-id")[:4],
        "offers": products.filter(old_price__isnull=False).order_by("-sold_count")[:4],
        "newest": products.order_by("-id")[:4],
        "categories": Category.objects.all(),
    })


def product_list(request):
    qs = Product.objects.filter(is_active=True).select_related("category")
    cat = request.GET.get("cat", "")
    q = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "new")
    if cat:
        qs = qs.filter(category__slug=cat)
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
    qs = qs.order_by({"low": "price", "high": "-price", "pop": "-sold_count"}.get(sort, "-id"))
    page = Paginator(qs, 12).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "shop/product_list.html", {
        "page": page, "categories": Category.objects.all(),
        "cat": cat, "q": q, "sort": sort, "qs_params": params.urlencode(),
    })


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    related = Product.objects.filter(category=product.category, is_active=True).exclude(pk=pk)[:4]
    return render(request, "shop/product_detail.html", {"product": product, "related": related})


def about(request):
    form = ContactForm()
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            ContactMessage.objects.create(**form.cleaned_data)
            messages.success(request, "پیام شما ارسال شد؛ به‌زودی پاسخ می‌دهیم.")
            return redirect("shop:about")
        messages.error(request, "نام و متن پیام را کامل وارد کنید.")
    return render(request, "shop/about.html", {"form": form, "provinces": shipping.PROVINCES})


# ---------- سبد خرید ----------
def cart_view(request):
    cart = Cart(request)
    return render(request, "shop/cart.html", {"cart": cart, "s": cart.summary()})


@require_POST
def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    if not product.in_stock:
        messages.error(request, "این محصول فعلاً موجود نیست.")
        return redirect(request.META.get("HTTP_REFERER") or "shop:product_list")
    try:
        qty = max(1, min(int(request.POST.get("qty", 1)), 20))
    except ValueError:
        qty = 1
    Cart(request).add(product, qty)
    messages.success(request, f"«{product.name}» به سبد خرید اضافه شد.")
    if request.POST.get("next") == "cart":
        return redirect("shop:cart")
    return redirect(request.META.get("HTTP_REFERER") or "shop:cart")


@require_POST
def cart_update(request):
    cart = Cart(request)
    if request.POST.get("remove"):
        cart.remove(request.POST["remove"])
    else:
        for key, value in request.POST.items():
            if key.startswith("qty_"):
                try:
                    product = Product.objects.get(pk=int(key[4:]), is_active=True)
                    cart.set_qty(product, int(value))
                except (ValueError, Product.DoesNotExist):
                    continue
        cart.set_gift(request.POST.get("gift_wrap") == "on", request.POST.get("gift_note", ""))
    if request.POST.get("go") == "checkout" and cart:
        return redirect("shop:checkout")
    return redirect("shop:cart")


# ---------- ثبت سفارش و پرداخت ----------
def checkout(request):
    cart = Cart(request)
    if not cart.lines():
        messages.info(request, "سبد خرید شما خالی است.")
        return redirect("shop:cart")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = create_order(cart, form.cleaned_data)
            request.session["last_customer"] = {
                k: form.cleaned_data[k] for k in ("name", "phone", "province", "city", "address", "postal_code")
            }
            return _start_payment(request, order)
    else:
        initial = request.session.get("last_customer", {})
        form = CheckoutForm(initial={**initial, "shipping_method": "post"})

    base = cart.summary()
    options = [
        {"key": k, **m, "cost": shipping.shipping_cost(k, base["subtotal"], base["weight"])}
        for k, m in shipping.METHODS.items()
    ]
    selected = form["shipping_method"].value() or "post"
    if selected not in shipping.METHODS:
        selected = "post"
    s = cart.summary(selected)
    return render(request, "shop/checkout.html", {
        "form": form, "s": s, "options": options, "selected": selected,
        "gateway": settings.PAYMENT_GATEWAY,
    })


def _start_payment(request, order):
    try:
        authority, url = get_gateway().request(request, order)
    except GatewayError as e:
        messages.error(request, str(e))
        return redirect(order)
    order.authority = authority
    order.payment_gateway = settings.PAYMENT_GATEWAY
    order.save(update_fields=["authority", "payment_gateway"])
    return HttpResponseRedirect(url)


@require_POST
def payment_start(request, code):
    order = get_object_or_404(Order, code=code, status=Order.Status.PENDING)
    return _start_payment(request, order)


def payment_callback(request):
    """آدرس بازگشت از درگاه: پرداخت را از سمت سرور تأیید می‌کند."""
    authority = request.GET.get("Authority", "")
    if not authority:
        raise Http404
    order = get_object_or_404(Order, authority=authority)
    if order.status != Order.Status.PENDING:
        return redirect(order)
    try:
        ok, ref_id = get_gateway().verify(request, order)
    except GatewayError as e:
        messages.error(request, str(e))
        return redirect(order)
    if not ok:
        messages.error(request, "پرداخت ناموفق بود یا لغو شد. مبلغی از حساب شما کسر نشده؛ در صورت کسر، تا ۷۲ ساعت برگشت می‌خورد.")
        return redirect(order)
    mark_paid(order.pk, ref_id)
    Cart(request).clear()
    messages.success(request, "پرداخت با موفقیت انجام شد.")
    return redirect(order)


def mock_bank(request, authority):
    """صفحه بانک آزمایشی؛ فقط وقتی PAYMENT_GATEWAY=mock است فعال است."""
    if settings.PAYMENT_GATEWAY != "mock":
        raise Http404
    order = get_object_or_404(Order, authority=authority, status=Order.Status.PENDING)
    if request.method == "POST":
        status = "OK" if request.POST.get("action") == "pay" else "NOK"
        return redirect(f"/payment/callback/?Authority={authority}&Status={status}")
    return render(request, "shop/mock_bank.html", {"order": order})


def order_detail(request, code):
    order = get_object_or_404(Order, code=code)
    return render(request, "shop/order_detail.html", {"order": order, "items": order.items.all()})


def track(request):
    form = TrackForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        order = Order.objects.filter(code=form.cleaned_data["code"], phone=form.cleaned_data["phone"]).first()
        if order:
            return redirect(order)
        messages.error(request, "سفارشی با این کد و شماره موبایل پیدا نشد.")
    return render(request, "shop/track.html", {"form": form})
