# Developed by AMIR AMMARZAD
from . import shipping
from .cart import Cart
from .models import Category


def store(request):
    return {
        "cart_count": Cart(request).count(),
        "nav_categories": Category.objects.all(),
        "FREE_SHIPPING_FROM": shipping.FREE_SHIPPING_FROM,
        "GIFT_WRAP_COST": shipping.GIFT_WRAP_COST,
        "SHIPPING_METHODS": shipping.METHODS.values(),
    }
