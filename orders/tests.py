from datetime import time

from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import Category, Order, OrderItem, Product


class OrderModelTest(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username='cliente', password='test-pass-123')
        self.order = Order.objects.create(
            customer=self.customer,
            pickup_time=time(10, 30),
            total_price=2500,
        )

    def test_order_creation(self):
        self.assertEqual(self.order.customer, self.customer)
        self.assertEqual(self.order.total_price, 2500)
        self.assertEqual(self.order.pickup_time, time(10, 30))
        self.assertIsNotNone(self.order.created_at)

    def test_order_str(self):
        self.assertEqual(str(self.order), f'Order #{self.order.pk} - cliente')


class OrderItemConstraintTest(TestCase):
    def setUp(self):
        customer = User.objects.create_user(username='cliente', password='test-pass-123')
        category = Category.objects.create(name='Bebidas')
        self.product = Product.objects.create(
            code='BEB001',
            name='Espresso',
            price=1200,
            stock=10,
            category=category,
        )
        self.order = Order.objects.create(
            customer=customer,
            pickup_time=time(10, 30),
            total_price=1200,
        )

    def test_product_can_only_appear_once_per_order(self):
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=1200,
            subtotal=1200,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OrderItem.objects.create(
                    order=self.order,
                    product=self.product,
                    quantity=2,
                    unit_price=1200,
                    subtotal=2400,
                )


class AuthenticationAndRoleTest(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            username='cliente',
            password='test-pass-123',
        )
        self.staff_user = User.objects.create_user(
            username='encargado',
            password='test-pass-123',
            is_staff=True,
        )

    def test_anonymous_users_are_redirected_to_login(self):
        for route_name in ('home', 'client_dashboard', 'staff_dashboard'):
            response = self.client.get(reverse(route_name))
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse('login'), response.url)

    def test_login_displays_username_and_role(self):
        response = self.client.post(
            reverse('login'),
            {'username': 'cliente', 'password': 'test-pass-123'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cliente')
        self.assertContains(response, 'Cliente')

    def test_roles_cannot_open_the_other_role_panel(self):
        self.client.force_login(self.client_user)
        self.assertEqual(self.client.get(reverse('staff_dashboard')).status_code, 403)

        self.client.force_login(self.staff_user)
        self.assertEqual(self.client.get(reverse('client_dashboard')).status_code, 403)

    def test_logout_ends_the_authenticated_session(self):
        self.client.force_login(self.client_user)
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        self.assertEqual(self.client.get(reverse('home')).status_code, 302)

    def test_session_expires_after_thirty_minutes_of_inactivity(self):
        self.assertEqual(settings.SESSION_COOKIE_AGE, 30 * 60)
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)


class ProductCatalogTest(TestCase):
    def setUp(self):
        customer = User.objects.create_user(username='catalogo', password='test-pass-123')
        self.client.force_login(customer)
        self.beverages = Category.objects.create(name='Bebidas', active=True)
        self.snacks = Category.objects.create(name='Snacks', active=True)
        inactive_category = Category.objects.create(name='Temporal', active=False)
        self.in_stock = Product.objects.create(
            code='BEB101', name='Espresso', price=1500, stock=5, category=self.beverages,
        )
        self.sold_out = Product.objects.create(
            code='BEB102', name='Jugo agotado', price=1200, stock=0, category=self.beverages,
        )
        Product.objects.create(
            code='SNK101', name='Brownie', price=950, stock=8, category=self.snacks,
        )
        Product.objects.create(
            code='SNK102', name='Producto oculto', price=1000, stock=8,
            available=False, category=self.snacks,
        )
        Product.objects.create(
            code='TMP101', name='Categoría inactiva', price=1000, stock=8,
            category=inactive_category,
        )

    def test_catalog_shows_only_available_products_in_active_categories(self):
        response = self.client.get(reverse('client_dashboard'))
        names = {product.name for product in response.context['products']}
        self.assertSetEqual(names, {'Espresso', 'Jugo agotado', 'Brownie'})

    def test_catalog_searches_by_product_name(self):
        response = self.client.get(reverse('client_dashboard'), {'q': 'espresso'})
        names = {product.name for product in response.context['products']}
        self.assertSetEqual(names, {'Espresso'})

    def test_catalog_filters_by_category(self):
        response = self.client.get(
            reverse('client_dashboard'),
            {'category': str(self.snacks.pk)},
        )
        names = {product.name for product in response.context['products']}
        self.assertSetEqual(names, {'Brownie'})

    def test_catalog_formats_prices_and_disables_sold_out_products(self):
        response = self.client.get(reverse('client_dashboard'))
        self.assertContains(response, '$1.500')
        self.assertContains(response, 'Agotado')
        self.assertNotContains(
            response,
            reverse('add_to_cart', args=[self.sold_out.pk]),
        )

    def test_sold_out_product_cannot_be_added_by_direct_post(self):
        response = self.client.post(reverse('add_to_cart', args=[self.sold_out.pk]))
        self.assertRedirects(response, reverse('client_dashboard'))
        self.assertNotIn(str(self.sold_out.pk), self.client.session.get('cart', {}))

    def test_cart_quantity_cannot_exceed_available_stock(self):
        add_url = reverse('add_to_cart', args=[self.in_stock.pk])
        for _ in range(self.in_stock.stock):
            self.client.post(add_url)

        response = self.client.post(add_url, follow=True)
        cart = self.client.session['cart']
        self.assertEqual(cart[str(self.in_stock.pk)], self.in_stock.stock)
        self.assertContains(response, 'No puedes agregar más unidades')
        self.assertContains(response, f'Carrito')