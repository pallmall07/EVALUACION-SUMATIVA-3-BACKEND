from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .auth_views import role_required
from .models import Order


@role_required(is_staff=False)
def client_order_history(request):
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})


@role_required(is_staff=False)
def client_order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        pk=order_id,
        customer=request.user,
    )
    return render(request, 'orders/order_detail.html', {'order': order})


@role_required(is_staff=False)
@require_POST
def cancel_pending_order(request, order_id):
    with transaction.atomic():
        order = get_object_or_404(
            Order.objects.select_for_update(),
            pk=order_id,
            customer=request.user,
        )
        if order.status != Order.STATUS_PENDING:
            messages.error(request, 'Solo puedes cancelar pedidos pendientes.')
        else:
            items = order.items.select_related('product').select_for_update()
            for item in items:
                item.product.stock += item.quantity
                item.product.save(update_fields=['stock'])
            order.status = Order.STATUS_CANCELLED
            order.save(update_fields=['status'])
            messages.success(request, 'Pedido cancelado; el stock fue repuesto.')
    return redirect('client_order_detail', order_id=order.pk)


@role_required(is_staff=True)
def staff_order_list(request):
    today = timezone.localdate()
    status = request.GET.get('status', '')
    valid_statuses = {value for value, _ in Order.STATUS_CHOICES}
    orders = Order.objects.filter(created_at__date=today)
    if status in valid_statuses:
        orders = orders.filter(status=status)
    orders = orders.select_related('customer').prefetch_related('items__product').order_by(
        'pickup_time', 'created_at'
    )
    return render(
        request,
        'orders/staff_orders.html',
        {
            'orders': orders,
            'selected_status': status if status in valid_statuses else '',
            'statuses': Order.STATUS_CHOICES,
            'today': today,
        },
    )


@role_required(is_staff=True)
@require_POST
def advance_order_status(request, order_id):
    with transaction.atomic():
        order = get_object_or_404(
            Order.objects.select_for_update(),
            pk=order_id,
            created_at__date=timezone.localdate(),
        )
        try:
            current_index = Order.STATUS_FLOW.index(order.status)
        except ValueError:
            messages.error(request, 'Este pedido no se puede avanzar desde su estado actual.')
        else:
            if current_index == len(Order.STATUS_FLOW) - 1:
                messages.error(request, 'El pedido ya fue entregado.')
            else:
                order.status = Order.STATUS_FLOW[current_index + 1]
                order.save(update_fields=['status'])
                messages.success(request, f'Pedido actualizado a {order.status}.')
    return redirect('staff_orders')