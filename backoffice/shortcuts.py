"""Helpers для backoffice-views.

- `backoffice_required` — decorator (`@login_required` + проверка `is_staff`).
- `region_scoped` — фильтр queryset под `request.user.manager_region`.
- `render_backoffice` — обёртка над `render` с авто-контекстом sidebar.
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .nav import build_nav


def backoffice_required(view_func):
    """Декоратор: требует login И is_staff.

    Не staff → redirect на login (а не 403). Это совместимо с UX backoffice
    как с отдельной поверхностью; обычный пользователь не должен «случайно»
    тыкнуть в /backoffice/.
    """
    @login_required(login_url='backoffice:login')
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('backoffice:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def region_scoped(qs, user, region_field='region'):
    """Возвращает queryset, отфильтрованный по `user.manager_region`.

    Поведение совпадает с `RegionScopedAdminMixin`:
    - `is_superuser=True` → полный qs
    - `manager_region` задан → фильтр по нему
    - иначе (staff без региона) → пустой qs
    """
    if user.is_superuser:
        return qs
    if getattr(user, 'manager_region_id', None):
        return qs.filter(**{f'{region_field}_id': user.manager_region_id})
    return qs.none()


def render_backoffice(request, template, *, active='', page_title='', context=None):
    """Render backoffice template с sidebar-контекстом.

    Args:
        active: id активного NAV-item (для подсветки).
        page_title: заголовок в topbar и <title>.
        context: доп. переменные шаблона.
    """
    ctx = {
        'bo_nav': build_nav(user=request.user),
        'bo_active': active,
        'bo_page_title': page_title,
    }
    if context:
        ctx.update(context)
    return render(request, template, ctx)
