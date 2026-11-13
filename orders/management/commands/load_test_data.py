from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from orders.models import Category, Product


class Command(BaseCommand):
    help = 'Load test data into the database'

    def handle(self, *args, **kwargs):
        categories = {
            name: Category.objects.get_or_create(name=name)[0]
            for name in ['Bebidas', 'Snacks', 'Sandwiches', 'Postres']
        }
        products = [
            ('Espresso', 'Café espresso recién preparado.', 1200, 20, True, 'Bebidas'),
            ('Americano', 'Café espresso diluido con agua caliente.', 1400, 20, True, 'Bebidas'),
            ('Capuccino', 'Café con leche vaporizada y espuma.', 1800, 15, True, 'Bebidas'),
            ('Latte', 'Café espresso con leche vaporizada.', 1900, 15, True, 'Bebidas'),
            ('Té negro', 'Té negro servido caliente.', 1100, 12, True, 'Bebidas'),
            ('Té chai', 'Té especiado con leche.', 1700, 10, True, 'Bebidas'),
            ('Chocolate caliente', 'Chocolate preparado con leche.', 1800, 10, True, 'Bebidas'),
            ('Jugo de naranja', 'Jugo de naranja en botella.', 1600, 0, False, 'Bebidas'),
            ('Galleta de avena', 'Galleta horneada de avena.', 700, 25, True, 'Snacks'),
            ('Brownie', 'Brownie de chocolate.', 1200, 16, True, 'Snacks'),
            ('Muffin de arándano', 'Muffin individual con arándanos.', 1300, 12, True, 'Snacks'),
            ('Empanada de queso', 'Empanada horneada rellena de queso.', 1500, 0, False, 'Snacks'),
            ('Barra de cereal', 'Barra de cereal y frutos secos.', 900, 18, True, 'Snacks'),
            ('Sandwich jamón queso', 'Pan, jamón y queso.', 2500, 15, True, 'Sandwiches'),
            ('Sandwich pollo palta', 'Pan con pollo y palta.', 3200, 12, True, 'Sandwiches'),
            ('Sandwich vegetariano', 'Pan con verduras frescas y queso.', 2800, 10, True, 'Sandwiches'),
            ('Sandwich ave mayo', 'Pan con ave y mayonesa.', 2900, 10, True, 'Sandwiches'),
            ('Sandwich de atún', 'Pan con atún y verduras.', 3000, 8, True, 'Sandwiches'),
            ('Sandwich queso tomate', 'Pan con queso y tomate.', 2400, 10, True, 'Sandwiches'),
            ('Kuchen de manzana', 'Porción de kuchen rellena de manzana.', 1800, 8, True, 'Postres'),
        ]
        for name, description, price, stock, available, category_name in products:
            Product.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
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