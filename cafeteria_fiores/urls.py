from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from orders import auth_views
from orders import order_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', auth_views.home, name='home'),
    path('encargado/', auth_views.staff_dashboard, name='staff_dashboard'),
    path('cliente/', auth_views.client_dashboard, name='client_dashboard'),
    path(
        'cliente/carrito/agregar/<int:product_id>/',
        auth_views.add_to_cart,
        name='add_to_cart',
    ),
    path('cliente/carrito/', auth_views.cart_view, name='cart'),
    path(
        'cliente/carrito/actualizar/<int:product_id>/',
        auth_views.update_cart,
        name='update_cart',
    ),
    path(
        'cliente/carrito/quitar/<int:product_id>/',
        auth_views.remove_from_cart,
        name='remove_from_cart',
    ),
    path('cliente/carrito/vaciar/', auth_views.clear_cart, name='clear_cart'),
    path('cliente/confirmar/', auth_views.checkout, name='checkout'),
    path('cliente/pedidos/', order_views.client_order_history, name='client_order_history'),
    path(
        'cliente/pedidos/<int:order_id>/',
        order_views.client_order_detail,
        name='client_order_detail',
    ),
    path(
        'cliente/pedidos/<int:order_id>/cancelar/',
        order_views.cancel_pending_order,
        name='cancel_pending_order',
    ),
    path('encargado/pedidos/', order_views.staff_order_list, name='staff_orders'),
    path(
        'encargado/pedidos/<int:order_id>/avanzar/',
        order_views.advance_order_status,
        name='advance_order_status',
    ),
]