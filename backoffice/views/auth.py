"""Auth views: login/logout для backoffice. `is_staff`-only — обычные
пользователи редиректятся обратно на login (см. `shortcuts.backoffice_required`).
"""

from django.contrib.auth import login as auth_login, logout as auth_logout
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods, require_POST

from ..forms import LoginForm


@never_cache
@csrf_protect
@require_http_methods(['GET', 'POST'])
def login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('backoffice:dashboard')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        auth_login(request, form.get_user())
        next_url = request.POST.get('next') or request.GET.get('next')
        return redirect(next_url or reverse('backoffice:dashboard'))

    return render(request, 'backoffice/login.html', {'form': form})


@require_POST
def logout(request):
    auth_logout(request)
    return redirect('backoffice:login')
