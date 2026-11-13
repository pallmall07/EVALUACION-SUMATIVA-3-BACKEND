from datetime import datetime, time
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

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
        self.assertContains(response, 'No hay stock suficiente de Espresso')
        self.assertContains(response, f'Carrito')


class CartAndCheckoutTest(TestCase):
    def setUp(self):
        customer = User.objects.create_user(username='pedido', password='test-pass-123')
        self.client.force_login(customer)
        category = Category.objects.create(name='Bebidas')
        self.espresso = Product.objects.create(
            code='CAF-101', name='Espresso', price=1500, stock=12, category=category,
        )
        self.latte = Product.objects.create(
            code='CAF-102', name='Latte', price=2200, stock=8, category=category,
        )

    def set_cart(self, items):
        session = self.client.session
        session['cart'] = {str(product_id): quantity for product_id, quantity in items.items()}
        session.save()

    def post_checkout(self, cart, pickup_time='10:30', observation=''):
        self.set_cart(cart)
        fixed_now = timezone.make_aware(datetime(2026, 1, 1, 10, 0))
        with patch('orders.forms.timezone.localtime', return_value=fixed_now):
            return self.client.post(
                reverse('checkout'),
                {'pickup_time': pickup_time, 'observation': observation},
                follow=True,
            )

    def test_cart_cannot_exceed_ten_units(self):
        add_url = reverse('add_to_cart', args=[self.espresso.pk])
        for _ in range(10):
            self.client.post(add_url)
        self.client.post(add_url)
        self.assertEqual(self.client.session['cart'][str(self.espresso.pk)], 10)

    def test_cart_quantity_can_be_updated_removed_and_cleared(self):
        self.set_cart({self.espresso.pk: 2, self.latte.pk: 1})
        self.client.post(
            reverse('update_cart', args=[self.espresso.pk]),
            {'quantity': '3'},
        )
        self.assertEqual(self.client.session['cart'][str(self.espresso.pk)], 3)

        self.client.post(reverse('remove_from_cart', args=[self.latte.pk]))
        self.assertNotIn(str(self.latte.pk), self.client.session['cart'])

        self.client.post(reverse('clear_cart'))
        self.assertEqual(self.client.session['cart'], {})

    def test_updating_quantity_cannot_push_cart_over_ten_units(self):
        self.set_cart({self.espresso.pk: 9, self.latte.pk: 1})
        response = self.client.post(
            reverse('update_cart', args=[self.espresso.pk]),
            {'quantity': '10'},
            follow=True,
        )
        self.assertEqual(self.client.session['cart'][str(self.espresso.pk)], 9)
        self.assertContains(response, 'no puede superar 10 unidades')

    def test_successful_checkout_creates_order_snapshots_prices_and_decrements_stock(self):
        response = self.post_checkout(
            {self.espresso.pk: 2, self.latte.pk: 1},
            observation='Sin azúcar',
        )
        order = Order.objects.get()
        self.espresso.refresh_from_db()
        self.latte.refresh_from_db()
        self.assertRedirects(response, reverse('client_dashboard'))
        self.assertEqual(order.status, 'Pendiente')
        self.assertEqual(order.total_price, 5200)
        self.assertEqual(order.observation, 'Sin azúcar')
        self.assertEqual(order.items.count(), 2)
        espresso_item = order.items.get(product=self.espresso)
        self.assertEqual(espresso_item.unit_price, 1500)
        self.assertEqual(espresso_item.subtotal, 3000)
        self.assertEqual(self.espresso.stock, 10)
        self.assertEqual(self.latte.stock, 7)
        self.assertEqual(self.client.session['cart'], {})

    def test_stock_shortage_creates_no_order_and_changes_no_product_stock(self):
        self.set_cart({self.espresso.pk: 2, self.latte.pk: 1})
        self.espresso.stock = 1
        self.espresso.save(update_fields=['stock'])
        self.assertContains(self.client.get(reverse('cart')), 'Continuar')
        response = self.post_checkout(
            {self.espresso.pk: 2, self.latte.pk: 1},
        )
        self.espresso.refresh_from_db()
        self.latte.refresh_from_db()
        self.assertFalse(Order.objects.exists())
        self.assertEqual(self.espresso.stock, 1)
        self.assertEqual(self.latte.stock, 8)
        self.assertEqual(self.client.session['cart'][str(self.espresso.pk)], 2)
        self.assertContains(response, 'No se creó el pedido')
        self.assertContains(response, 'Espresso')

    def test_invalid_pickup_time_keeps_order_uncreated_and_cart_intact(self):
        response = self.post_checkout({self.espresso.pk: 1}, pickup_time='10:19')
        self.assertFalse(Order.objects.exists())
        self.assertEqual(self.client.session['cart'][str(self.espresso.pk)], 1)
        self.assertContains(response, 'al menos 20 minutos')

    def test_pickup_time_must_be_within_business_hours(self):
        for pickup_time in ('07:59', '18:01'):
            response = self.post_checkout(
                {self.espresso.pk: 1},
                pickup_time=pickup_time,
            )
            self.assertFalse(Order.objects.exists())
            self.assertContains(response, 'entre las 08:00 y las 18:00')