# Developed by AMIR AMMARZAD
"""سبد خرید مبتنی بر session."""
from decimal import Decimal

from . import shipping
from .models import Product


class Cart:
    KEY = "cart"

    def __init__(self, request):
        self.session = request.session
        self.data = self.session.get(self.KEY, {})

    def _save(self):
        self.session[self.KEY] = self.data
        self.session.modified = True

    def __bool__(self):
        return bool(self.data)

    def count(self):
        return sum(self.data.values())

    def add(self, product, qty=1):
        cur = self.data.get(str(product.pk), 0) + qty
        self.data[str(product.pk)] = max(1, min(cur, product.stock))
        self._save()

    def set_qty(self, product, qty):
        if qty <= 0:
            self.remove(product.pk)
            return
        self.data[str(product.pk)] = min(qty, product.stock) or 1
        self._save()

    def remove(self, pk):
        self.data.pop(str(pk), None)
        self._save()

    def clear(self):
        self.session.pop(self.KEY, None)
        self.session.pop("gift_wrap", None)
        self.session.pop("gift_note", None)
        self.session.modified = True
        self.data = {}

    # بسته‌بندی کادویی
    @property
    def gift_wrap(self):
        return bool(self.session.get("gift_wrap", False))

    @property
    def gift_note(self):
        return self.session.get("gift_note", "")

    def set_gift(self, wrap, note):
        self.session["gift_wrap"] = bool(wrap)
        self.session["gift_note"] = (note or "").strip()[:200]
        self.session.modified = True

    def lines(self):
        """لیست آیتم‌ها؛ محصولات حذف‌شده یا غیرفعال خودکار از سبد پاک می‌شوند."""
        ids = [int(i) for i in self.data]
        products = {p.pk: p for p in Product.objects.filter(pk__in=ids, is_active=True)}
        out = []
        for pid, qty in list(self.data.items()):
            p = products.get(int(pid))
            if not p or p.stock <= 0:
                self.data.pop(pid)
                self._save()
                continue
            qty = min(qty, p.stock)
            out.append({"product": p, "qty": qty, "total": p.price * qty})
        return out

    def summary(self, method=None):
        lines = self.lines()
        subtotal = sum(l["total"] for l in lines)
        weight = sum((l["product"].weight_kg * l["qty"] for l in lines), Decimal(0))
        saving = sum(
            max(0, (l["product"].old_price or l["product"].price) - l["product"].price) * l["qty"]
            for l in lines
        )
        wrap_cost = shipping.GIFT_WRAP_COST if (self.gift_wrap and lines) else 0
        ship_cost = shipping.shipping_cost(method, subtotal, weight) if (method and lines) else 0
        return {
            "lines": lines, "subtotal": subtotal, "weight": weight, "saving": saving,
            "wrap_cost": wrap_cost, "shipping_cost": ship_cost,
            "total": subtotal + wrap_cost + ship_cost,
        }
