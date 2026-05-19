"""Раздел «Сайт» → «Меню» (NavSection + NavItem CMS).

Только для superuser — `@superuser_required` на каждой view.

Структура: список секций (table) → edit секции с inline NavItem formset.
NavItem можно добавлять через `extra=1` или удалять через checkbox `DELETE`.
Перенос пункта между секциями — отдельный select `section` на edit (но в
inline-formset родителя `section` зафиксирован, поэтому перенос делается
через прямое редактирование item'а — пока вне UI; для редко-используемой
операции достаточно admin'а).
"""

import json

from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from navigation.models import NavItem, NavSection

from ..forms import (
    NavItemFormSet,
    NavSectionCreateForm,
    NavSectionEditForm,
    TRANSLATION_LANGS,
)
from ..shortcuts import render_backoffice, superuser_required


@never_cache
@superuser_required
def site_menu_list(request):
    """Таблица секций с count'ом пунктов + кнопка «Добавить секцию»."""
    sections = list(
        NavSection.objects.annotate(item_count=Count('items')).order_by('order', 'slug')
    )
    return render_backoffice(
        request,
        'backoffice/site/menu/list.html',
        active='navigation',
        page_title='Меню',
        context={'sections': sections},
    )


@never_cache
@superuser_required
def site_menu_create(request):
    """Форма создания секции. После save → redirect на edit."""
    if request.method == 'POST':
        form = NavSectionCreateForm(request.POST)
        if form.is_valid():
            section = form.save()
            messages.success(request, f'Секция «{section.label}» создана.')
            return redirect('backoffice:site_menu_edit', pk=section.pk)
    else:
        form = NavSectionCreateForm()

    return render_backoffice(
        request,
        'backoffice/site/menu/create.html',
        active='navigation',
        page_title='Меню · новая секция',
        context={'form': form},
    )


@never_cache
@superuser_required
def site_menu_edit(request, pk):
    """Редактирование секции + inline NavItem'ы. Inline = extra=1 + can_delete."""
    section = get_object_or_404(NavSection, pk=pk)

    if request.method == 'POST':
        form = NavSectionEditForm(request.POST, instance=section)
        formset = NavItemFormSet(request.POST, instance=section, prefix='items')
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'Секция «{section.label}» сохранена.')
            return redirect('backoffice:site_menu_edit', pk=section.pk)
    else:
        form = NavSectionEditForm(instance=section)
        formset = NavItemFormSet(instance=section, prefix='items')

    item_translatable_bases = ['label']
    section_translatable_bases = ['label']

    return render_backoffice(
        request,
        'backoffice/site/menu/edit.html',
        active='navigation',
        page_title=f'Меню · {section.label}',
        context={
            'section': section,
            'form': form,
            'formset': formset,
            'translation_langs': TRANSLATION_LANGS,
            'section_translatable_bases_json': json.dumps(section_translatable_bases),
            'item_translatable_bases_json': json.dumps(item_translatable_bases),
        },
    )


@require_POST
@superuser_required
def site_menu_delete(request, pk):
    """Удаление секции. Каскадно удалит NavItem'ы — об этом предупреждает
    JS-confirm в шаблоне (на NavSection on_delete=CASCADE)."""
    section = get_object_or_404(NavSection, pk=pk)
    label = section.label
    items_count = section.items.count()
    section.delete()
    messages.success(
        request,
        f'Секция «{label}» удалена. Также удалено пунктов: {items_count}.',
    )
    return redirect('backoffice:site_menu_list')


@require_POST
@superuser_required
def site_menu_item_delete(request, pk):
    """Точечное удаление пункта (вне formset'а). Используется со страницы edit
    через POST + redirect обратно."""
    item = get_object_or_404(NavItem, pk=pk)
    section_pk = item.section_id
    label = item.label
    item.delete()
    messages.success(request, f'Пункт «{label}» удалён.')
    return redirect('backoffice:site_menu_edit', pk=section_pk)
