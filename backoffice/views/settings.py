"""Раздел «Настройки» → «Регионы» и «Пользователи».

Только для superuser. Регионы — справочник филиалов; Пользователи — staff
аккаунты для backoffice (+ редко: суперадмины и менеджеры с regional scope).

Удаление региона CASCADE'ит на весь контент региона (HomePage, BlogPost,
NavItem.flat_page и т.п.) — ставим JS-confirm + блокируем при наличии
менеджеров с manager_region == этот регион.

Удаление пользователя — стандартный delete. Свой собственный аккаунт удалить
нельзя (защита от случайной самоблокировки).
"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from regions.models import Region

from ..forms import (
    RegionCreateForm,
    RegionEditForm,
    ROLE_DESCRIPTIONS,
    TRANSLATION_LANGS,
    UserCreateForm,
    UserEditForm,
    UserPasswordForm,
)
from ..shortcuts import render_backoffice, superuser_required


User = get_user_model()


# ----- Регионы --------------------------------------------------------------


@never_cache
@superuser_required
def settings_regions_list(request):
    rows = list(
        Region.objects.annotate(manager_count=Count('managers'))
        .order_by('-is_active', '-is_default', 'slug')
    )
    return render_backoffice(
        request,
        'backoffice/settings/regions/list.html',
        active='regions',
        page_title='Регионы',
        context={'rows': rows},
    )


@never_cache
@superuser_required
def settings_regions_create(request):
    if request.method == 'POST':
        form = RegionCreateForm(request.POST)
        if form.is_valid():
            region = form.save()
            messages.success(request, f'Регион «{region.name}» создан.')
            return redirect('backoffice:settings_regions_edit', pk=region.pk)
    else:
        form = RegionCreateForm()

    return render_backoffice(
        request,
        'backoffice/settings/regions/create.html',
        active='regions',
        page_title='Регионы · новый',
        context={'form': form},
    )


@never_cache
@superuser_required
def settings_regions_edit(request, pk):
    region = get_object_or_404(Region, pk=pk)

    if request.method == 'POST':
        form = RegionEditForm(request.POST, instance=region)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Регион «{region.name}» сохранён.')
                return redirect('backoffice:settings_regions_edit', pk=region.pk)
            except IntegrityError:
                # UniqueConstraint where is_default=True — пытаемся поставить
                # второй default.
                form.add_error(
                    'is_default',
                    'Уже есть регион по умолчанию. Сначала сними флаг с предыдущего.',
                )
    else:
        form = RegionEditForm(instance=region)

    return render_backoffice(
        request,
        'backoffice/settings/regions/edit.html',
        active='regions',
        page_title=f'Регион · {region.name}',
        context={
            'region': region,
            'form': form,
            'translation_langs': TRANSLATION_LANGS,
            'translatable_bases': ['name'],
        },
    )


@require_POST
@superuser_required
def settings_regions_delete(request, pk):
    region = get_object_or_404(Region, pk=pk)
    if region.is_default:
        messages.error(
            request,
            f'Нельзя удалить «{region.name}» — это регион по умолчанию. '
            'Сначала переключите default на другой регион.',
        )
        return redirect('backoffice:settings_regions_edit', pk=region.pk)
    managers_count = region.managers.count()
    if managers_count:
        messages.error(
            request,
            f'Нельзя удалить «{region.name}» — к нему привязано менеджеров: {managers_count}. '
            'Переведите или удалите этих пользователей сначала.',
        )
        return redirect('backoffice:settings_regions_edit', pk=region.pk)
    name = region.name
    region.delete()
    messages.success(request, f'Регион «{name}» удалён.')
    return redirect('backoffice:settings_regions_list')


# ----- Пользователи ---------------------------------------------------------


@never_cache
@superuser_required
def settings_users_list(request):
    rows = list(
        User.objects.select_related('manager_region')
        .order_by('-is_active', '-is_superuser', '-is_staff', 'username')
    )
    return render_backoffice(
        request,
        'backoffice/settings/users/list.html',
        active='users',
        page_title='Пользователи',
        context={'rows': rows},
    )


@never_cache
@superuser_required
def settings_users_create(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Пользователь «{user.username}» создан.')
            return redirect('backoffice:settings_users_edit', pk=user.pk)
    else:
        form = UserCreateForm()

    return render_backoffice(
        request,
        'backoffice/settings/users/create.html',
        active='users',
        page_title='Пользователи · новый',
        context={
            'form': form,
            'role_descriptions': ROLE_DESCRIPTIONS,
        },
    )


@never_cache
@superuser_required
def settings_users_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    is_self = user.pk == request.user.pk

    if request.method == 'POST':
        # lock_role=True при редактировании своего аккаунта — защита от
        # самоблокировки (нельзя снять is_superuser у себя).
        form = UserEditForm(request.POST, instance=user, lock_role=is_self)
        if form.is_valid():
            if is_self:
                # Дополнительная защита: is_active нельзя снять у себя
                # (вдруг role сохранил superadmin, но галку Active снял).
                form.instance.is_active = True
            form.save()
            messages.success(request, f'Пользователь «{user.username}» сохранён.')
            return redirect('backoffice:settings_users_edit', pk=user.pk)
    else:
        form = UserEditForm(instance=user, lock_role=is_self)

    password_form = UserPasswordForm(user=user)

    return render_backoffice(
        request,
        'backoffice/settings/users/edit.html',
        active='users',
        page_title=f'Пользователь · {user.username}',
        context={
            'user_obj': user,
            'form': form,
            'password_form': password_form,
            'is_self': is_self,
            'role_descriptions': ROLE_DESCRIPTIONS,
        },
    )


@require_POST
@superuser_required
def settings_users_password(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = UserPasswordForm(request.POST, user=user)
    if form.is_valid():
        form.save()
        messages.success(request, f'Пароль пользователя «{user.username}» обновлён.')
        return redirect('backoffice:settings_users_edit', pk=user.pk)
    is_self = user.pk == request.user.pk
    edit_form = UserEditForm(instance=user, lock_role=is_self)
    return render_backoffice(
        request,
        'backoffice/settings/users/edit.html',
        active='users',
        page_title=f'Пользователь · {user.username}',
        context={
            'user_obj': user,
            'form': edit_form,
            'password_form': form,
            'is_self': is_self,
            'password_open': True,
            'role_descriptions': ROLE_DESCRIPTIONS,
        },
    )


@require_POST
@superuser_required
def settings_users_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.pk == request.user.pk:
        messages.error(request, 'Нельзя удалить собственный аккаунт.')
        return redirect('backoffice:settings_users_edit', pk=user.pk)
    username = user.username
    user.delete()
    messages.success(request, f'Пользователь «{username}» удалён.')
    return redirect('backoffice:settings_users_list')
