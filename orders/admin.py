from django.contrib import admin
from .models import Category, Product, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'active')
    list_filter = ('active',)
    search_fields = ('name', 'description')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'category', 'price', 'stock', 'available', 'created_at')
    list_filter = ('available', 'category')
    search_fields = ('code', 'name', 'category__name')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'quantity', 'unit_price', 'subtotal')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'created_at', 'pickup_time', 'status', 'total_price')
    list_filter = ('status', 'created_at', 'pickup_time')
    search_fields = ('customer__username',)
    inlines = [OrderItemInline]