from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render


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
    return render(request, 'orders/client_dashboard.html')
