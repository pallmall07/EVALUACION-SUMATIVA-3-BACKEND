from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import OrderConfirmationForm
from .models import Category, Order, OrderItem, Product


MAX_CART_UNITS = 10


def role_required(is_staff):
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.user.is_staff != is_staff:
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


@login_required
def home(request):
    if request.user.is_staff:
        return redirect('staff_dashboard')
    return redirect('client_dashboard')


@role_required(is_staff=True)
def staff_dashboard(request):
    return render(request, 'orders/staff_dashboard.html')


def _get_cart(request):
    cart = request.session.get('cart', {})
    return {
        str(product_id): int(quantity)
        for product_id, quantity in cart.items()
        if int(quantity) > 0
    }


def _get_cart_items(cart):
    products = Product.objects.select_related('category').in_bulk(
        [int(product_id) for product_id in cart]
    )
    items = []
    total = 0
    for product_id, quantity in cart.items():
        product = products.get(int(product_id))
        if product is None:
            items.append({
                'product_id': product_id,
                'name': 'Producto no disponible',
                'quantity': quantity,
                'subtotal': 0,
                'can_order': False,
            })
            continue

        subtotal = product.price * quantity
        total += subtotal
        items.append({
            'product_id': product_id,
            'product': product,
            'name': product.name,
            'quantity': quantity,
            'subtotal': subtotal,
            'can_order': product.available and product.category.active and product.stock >= quantity,
        })
    return items, total


@role_required(is_staff=False)
def client_dashboard(request):
    categories = Category.objects.filter(active=True).order_by('name')
    products = Product.objects.filter(
        available=True,
        category__active=True,
    ).select_related('category').order_by('name')
    search = request.GET.get('q', '').strip()
    selected_category = request.GET.get('category', '').strip()

    if search:
        products = products.filter(name__icontains=search)

    if selected_category:
        try:
            category_id = int(selected_category)
        except ValueError:
            selected_category = ''
        else:
            if categories.filter(pk=category_id).exists():
                products = products.filter(category_id=category_id)
            else:
                selected_category = ''

    cart = _get_cart(request)
    cart_count = sum(int(quantity) for quantity in cart.values())
    return render(
        request,
        'orders/client_dashboard.html',
        {
            'categories': categories,
            'products': products,
            'search': search,
            'selected_category': selected_category,
            'cart_count': cart_count,
        },
    )


@role_required(is_staff=False)
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(
        Product,
        pk=product_id,
        available=True,
        category__active=True,
    )
    if product.stock <= 0:
        messages.error(request, f'{product.name} está agotado y no se agregó al carrito.')
        return redirect('client_dashboard')

    cart = _get_cart(request)
    product_key = str(product.pk)
    quantity = int(cart.get(product_key, 0))
    cart_count = sum(cart.values())
    if quantity >= product.stock:
        messages.error(request, f'No hay stock suficiente de {product.name}.')
        return redirect('client_dashboard')
    if cart_count >= MAX_CART_UNITS:
        messages.error(request, 'El carrito no puede superar 10 unidades en total.')
        return redirect('client_dashboard')

    cart[product_key] = quantity + 1
    request.session['cart'] = cart
    messages.success(request, f'{product.name} se agregó al carrito.')
    return redirect('client_dashboard')


@role_required(is_staff=False)
def cart_view(request):
    cart = _get_cart(request)
    items, total = _get_cart_items(cart)
    cart_count = sum(cart.values())
    return render(
        request,
        'orders/cart.html',
        {
            'items': items,
            'cart_count': cart_count,
            'cart_total': total,
            'can_checkout': bool(items) and cart_count <= MAX_CART_UNITS,
        },
    )


@role_required(is_staff=False)
@require_POST
def update_cart(request, product_id):
    cart = _get_cart(request)
    product_key = str(product_id)
    try:
        quantity = int(request.POST.get('quantity', ''))
    except ValueError:
        messages.error(request, 'Ingresa una cantidad válida.')
        return redirect('cart')

    if quantity < 0:
        messages.error(request, 'La cantidad no puede ser negativa.')
        return redirect('cart')
    if quantity == 0:
        cart.pop(product_key, None)
        request.session['cart'] = cart
        messages.success(request, 'Producto quitado del carrito.')
        return redirect('cart')

    product = Product.objects.filter(
        pk=product_id,
        available=True,
        category__active=True,
    ).first()
    other_units = sum(value for key, value in cart.items() if key != product_key)
    if product is None or quantity > product.stock:
        messages.error(request, 'El producto no está disponible en esa cantidad.')
    elif other_units + quantity > MAX_CART_UNITS:
        messages.error(request, 'El carrito no puede superar 10 unidades en total.')
    else:
        cart[product_key] = quantity
        request.session['cart'] = cart
        messages.success(request, 'Cantidad actualizada.')
    return redirect('cart')


@role_required(is_staff=False)
@require_POST
def remove_from_cart(request, product_id):
    cart = _get_cart(request)
    cart.pop(str(product_id), None)
    request.session['cart'] = cart
    messages.success(request, 'Producto quitado del carrito.')
    return redirect('cart')


@role_required(is_staff=False)
@require_POST
def clear_cart(request):
    request.session['cart'] = {}
    messages.success(request, 'Carrito vaciado.')
    return redirect('cart')


@role_required(is_staff=False)
def checkout(request):
    cart = _get_cart(request)
    if not cart:
        messages.error(request, 'Agrega productos antes de confirmar el pedido.')
        return redirect('cart')
    if sum(cart.values()) > MAX_CART_UNITS:
        messages.error(request, 'El carrito no puede superar 10 unidades en total.')
        return redirect('cart')

    form = OrderConfirmationForm(request.POST or None)
    items, total = _get_cart_items(cart)
    if request.method == 'POST' and form.is_valid():
        product_ids = [int(product_id) for product_id in cart]
        with transaction.atomic():
            products = Product.objects.select_for_update().select_related('category').filter(
                pk__in=product_ids,
            )
            product_map = {str(product.pk): product for product in products}
            unavailable = []
            for product_id, quantity in cart.items():
                product = product_map.get(product_id)
                if (
                    product is None
                    or not product.available
                    or not product.category.active
                    or product.stock < quantity
                ):
                    unavailable.append(product.name if product else 'producto eliminado')

            if unavailable:
                messages.error(
                    request,
                    f"No se creó el pedido. Stock insuficiente o producto no disponible: {', '.join(unavailable)}.",
                )
                return redirect('cart')

            order_total = sum(product_map[key].price * quantity for key, quantity in cart.items())
            order = Order.objects.create(
                customer=request.user,
                pickup_time=form.cleaned_data['pickup_time'],
                status='Pendiente',
                total_price=order_total,
                observation=form.cleaned_data['observation'],
            )
            for product_id, quantity in cart.items():
                product = product_map[product_id]
                unit_price = product.price
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=unit_price * quantity,
                )
                product.stock -= quantity
                product.save(update_fields=['stock'])

        request.session['cart'] = {}
        messages.success(request, f'Pedido #{order.pk} confirmado.')
        return redirect('client_dashboard')

    return render(
        request,
        'orders/checkout.html',
        {
            'form': form,
            'items': items,
            'cart_count': sum(cart.values()),
            'cart_total': total,
        },
    )
