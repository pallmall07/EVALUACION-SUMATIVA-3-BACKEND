from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import Order


class OrderModelTest(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username='cliente', password='test-pass-123')
        self.order = Order.objects.create(
            customer=self.customer,
            pickup_time=timezone.now(),
            total_price=Decimal('2500.00'),
        )

    def test_order_creation(self):
        self.assertEqual(self.order.customer, self.customer)
        self.assertEqual(self.order.total_price, Decimal('2500.00'))
        self.assertIsNotNone(self.order.created_at)

    def test_order_str(self):
        self.assertEqual(str(self.order), f'Order #{self.order.pk} - cliente')