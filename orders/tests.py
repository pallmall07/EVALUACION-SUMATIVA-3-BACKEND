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