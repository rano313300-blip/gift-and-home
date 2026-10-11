# Developed by AMIR AMMARZAD
from django.urls import path

from . import views

app_name = "shop"

urlpatterns = [
    path("", views.home, name="home"),
    path("shop/", views.product_list, name="product_list"),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:pk>/", views.cart_add, name="cart_add"),
    path("cart/update/", views.cart_update, name="cart_update"),
    path("checkout/", views.checkout, name="checkout"),
    path("payment/start/<str:code>/", views.payment_start, name="payment_start"),
    path("payment/callback/", views.payment_callback, name="payment_callback"),
    path("payment/mock/<str:authority>/", views.mock_bank, name="mock_bank"),
    path("order/<str:code>/", views.order_detail, name="order_detail"),
    path("track/", views.track, name="track"),
    path("about/", views.about, name="about"),
]
