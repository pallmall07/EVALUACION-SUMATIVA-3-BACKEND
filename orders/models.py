from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True, db_column='nombre')
    description = models.TextField(blank=True, db_column='descripcion')
    active = models.BooleanField(default=True, db_column='activa')

    def __str__(self):
        return self.name

class Product(models.Model):
    code = models.CharField(max_length=10, unique=True, db_column='codigo')
    name = models.CharField(max_length=100, db_column='nombre')
    price = models.IntegerField(db_column='precio')
    stock = models.IntegerField(default=0)
    available = models.BooleanField(default=True, db_column='disponible')
    created_at = models.DateTimeField(default=timezone.now, db_column='creado')
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        db_column='categoria_id',
    )

    def __str__(self):
        return self.name

class Order(models.Model):
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        db_column='cliente_id',
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='fecha')
    pickup_time = models.TimeField(db_column='hora_retiro')
    status = models.CharField(max_length=15, default='pendiente', db_column='estado')
    total_price = models.IntegerField(db_column='total')
    observation = models.TextField(blank=True, db_column='observacion')

    def __str__(self):
        return f"Order #{self.id} - {self.customer.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        db_column='pedido_id',
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT, db_column='producto_id')
    quantity = models.IntegerField(db_column='cantidad')
    unit_price = models.IntegerField(default=0, db_column='precio_unitario')
    subtotal = models.IntegerField(default=0, db_column='subtotal')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('order', 'product'), name='unique_order_product'),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"