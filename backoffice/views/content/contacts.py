"""ContactsPage edit + inline Departments + AI-translate/SEO."""

import json

from django.contrib import messages
from django.db.models import Count
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from pages.models import ContactsPage

from ...forms import (
    CONTACTS_TRANSLATABLE,
    ContactsDepartmentFormSet,
    ContactsPageEditForm,
    TRANSLATION_LANGS,
)
from ...shortcuts import backoffice_required, region_scoped, render_backoffice
from .._common import (
    get_for_user_or_404,
    make_readonly_step,
    make_step,
    run_seo,
    run_translate,
)


@never_cache
@backoffice_required
def content_contacts_list(request):
    qs = (
        region_scoped(ContactsPage.objects.select_related('region'), request.user)
        .annotate(department_count=Count('departments'))
        .order_by('region__name')
    )
    return render_backoffice(
        request,
        'backoffice/content/contacts/list.html',
        active='contacts',
        page_title='Контакты',
        context={'rows': qs},
    )


def _get_contacts_for_user(request, pk):
    return get_for_user_or_404(ContactsPage.objects.all(), request, pk)


def _contactspage_steps(contacts):
    """Stepper completeness для ContactsPage. Departments — read-only счётчик
    (JS не отслеживает изменения inline-formset на лету)."""
    ru_fields = [
        'intro_title_ru',
        'intro_text_ru',
        'office_name_ru',
        'office_address_ru',
        'office_hours_ru',
        'latitude',
        'longitude',
    ]
    kk_fields = [
        'intro_title_kk', 'intro_text_kk',
        'office_name_kk', 'office_address_kk', 'office_hours_kk',
    ]
    en_fields = [
        'intro_title_en', 'intro_text_en',
        'office_name_en', 'office_address_en', 'office_hours_en',
    ]
    seo_fields = [
        'seo_title_ru', 'seo_description_ru', 'og_title_ru', 'og_description_ru',
    ]
    dept_total = contacts.departments.count()
    dept_filled = sum(
        1 for d in contacts.departments.all()
        if (d.title or '').strip() and (d.description or '').strip()
        and ((d.phone or '').strip() or (d.email or '').strip())
    )

    return [
        make_step(contacts, id='ru', label='Основа (RU)', fields=ru_fields, required=True),
        make_step(contacts, id='kk', label='Перевод KZ', fields=kk_fields),
        make_step(contacts, id='en', label='Перевод EN', fields=en_fields),
        make_step(contacts, id='seo', label='SEO', fields=seo_fields),
        make_readonly_step(id='departments', label='Отделы', filled=dept_filled, total=dept_total),
    ]


@never_cache
@backoffice_required
def content_contacts_edit(request, pk):
    contacts = _get_contacts_for_user(request, pk)

    if request.method == 'POST':
        form = ContactsPageEditForm(request.POST, request.FILES, instance=contacts)
        formset = ContactsDepartmentFormSet(request.POST, instance=contacts, prefix='departments')
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Страница «Контакты» сохранена.')
            return redirect('backoffice:content_contacts_edit', pk=contacts.pk)
    else:
        form = ContactsPageEditForm(instance=contacts)
        formset = ContactsDepartmentFormSet(instance=contacts, prefix='departments')

    steps = _contactspage_steps(contacts)

    # Bases для inline-departments auto-translate. Каждая форма формсета имеет
    # отдельный prefix `departments-N-*`, frontend Alpine находит их по
    # data-form-id + data-prefix.
    department_translatable_bases = ['title', 'description', 'hours']

    return render_backoffice(
        request,
        'backoffice/content/contacts/edit.html',
        active='contacts',
        page_title=f'Контакты — {contacts.region.name}',
        context={
            'contacts': contacts,
            'form': form,
            'formset': formset,
            'translation_langs': TRANSLATION_LANGS,
            'steps_json': json.dumps(steps),
            'translatable_bases_json': json.dumps(list(CONTACTS_TRANSLATABLE)),
            'department_translatable_bases_json': json.dumps(department_translatable_bases),
        },
    )


@require_POST
@backoffice_required
def content_contacts_translate(request, pk):
    _get_contacts_for_user(request, pk)
    return run_translate(request)


@require_POST
@backoffice_required
def content_contacts_seo(request, pk):
    _get_contacts_for_user(request, pk)
    return run_seo(request, empty_hint='Заполни хотя бы intro_title/intro_text на RU.')
