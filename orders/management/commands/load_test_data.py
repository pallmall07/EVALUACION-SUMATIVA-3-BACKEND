from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from orders.models import Category, Product


class Command(BaseCommand):
    help = 'Load test data into the database'

    def handle(self, *args, **kwargs):
        category_data = {
            'Bebidas': 'Bebidas calientes y frías.',
            'Snacks': 'Colaciones y productos individuales.',
            'Sandwiches': 'Preparaciones saladas para llevar.',
            'Postres': 'Dulces y preparaciones de repostería.',
        }
        categories = {}
        for name, description in category_data.items():
            categories[name], _ = Category.objects.update_or_create(
                name=name,
                defaults={'description': description, 'active': True},
            )

        products = [
            ('BEB001', 'Espresso', 1200, 20, True, 'Bebidas'),
            ('BEB002', 'Americano', 1400, 20, True, 'Bebidas'),
            ('BEB003', 'Capuccino', 1800, 15, True, 'Bebidas'),
            ('BEB004', 'Latte', 1900, 15, True, 'Bebidas'),
            ('BEB005', 'Té negro', 1100, 12, True, 'Bebidas'),
            ('BEB006', 'Té chai', 1700, 10, True, 'Bebidas'),
            ('BEB007', 'Chocolate caliente', 1800, 10, True, 'Bebidas'),
            ('BEB008', 'Jugo de naranja', 1600, 0, False, 'Bebidas'),
            ('SNK001', 'Galleta de avena', 700, 25, True, 'Snacks'),
            ('SNK002', 'Brownie', 1200, 16, True, 'Snacks'),
            ('SNK003', 'Muffin de arándano', 1300, 12, True, 'Snacks'),
            ('SNK004', 'Empanada de queso', 1500, 0, False, 'Snacks'),
            ('SNK005', 'Barra de cereal', 900, 18, True, 'Snacks'),
            ('SAN001', 'Sandwich jamón queso', 2500, 15, True, 'Sandwiches'),
            ('SAN002', 'Sandwich pollo palta', 3200, 12, True, 'Sandwiches'),
            ('SAN003', 'Sandwich vegetariano', 2800, 10, True, 'Sandwiches'),
            ('SAN004', 'Sandwich ave mayo', 2900, 10, True, 'Sandwiches'),
            ('SAN005', 'Sandwich de atún', 3000, 8, True, 'Sandwiches'),
            ('SAN006', 'Sandwich queso tomate', 2400, 10, True, 'Sandwiches'),
            ('POS001', 'Kuchen de manzana', 1800, 8, True, 'Postres'),
        ]
        for code, name, price, stock, available, category_name in products:
            Product.objects.update_or_create(
                name=name,
                defaults={
                    'code': code,
                    'price': price,
                    'stock': stock,
                    'available': available,
                    'category': categories[category_name],
                },
            )

        demo_users = [
            ('encargado', 'encargado@fiores.local', True, True),
            ('cliente1', 'cliente1@fiores.local', False, False),
            ('cliente2', 'cliente2@fiores.local', False, False),
        ]
        for username, email, is_staff, is_superuser in demo_users:
            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': is_staff,
                    'is_superuser': is_superuser,
                    'is_active': True,
                },
            )
            user.set_password('FioresDemo2026!')
            user.save(update_fields=['password'])

        self.stdout.write(self.style.SUCCESS('Test data loaded: 4 categories, 20 products and 3 users.'))