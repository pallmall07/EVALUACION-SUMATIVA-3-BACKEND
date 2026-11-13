from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Category, Product


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

    cart = request.session.get('cart', {})
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

    cart = request.session.get('cart', {})
    product_key = str(product.pk)
    quantity = int(cart.get(product_key, 0))
    if quantity >= product.stock:
        messages.error(request, 'No puedes agregar más unidades que las disponibles.')
        return redirect('client_dashboard')

    cart[product_key] = quantity + 1
    request.session['cart'] = cart
    messages.success(request, f'{product.name} se agregó al carrito.')
    return redirect('client_dashboard')
