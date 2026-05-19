"""FooterPage edit — текст под лого + URL соцсетей. Singleton per region."""

import json

from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from pages.models import FooterPage

from ...forms import (
    FOOTER_TRANSLATABLE,
    FooterPageEditForm,
    TRANSLATION_LANGS,
)
from ...shortcuts import backoffice_required, region_scoped, render_backoffice
from .._common import (
    get_for_user_or_404,
    make_step,
    run_translate,
)


@never_cache
@backoffice_required
def content_footer_list(request):
    qs = (
        region_scoped(FooterPage.objects.select_related('region'), request.user)
        .order_by('region__name')
    )
    return render_backoffice(
        request,
        'backoffice/content/footer/list.html',
        active='footer',
        page_title='Футер',
        context={'rows': qs},
    )


def _get_footer_for_user(request, pk):
    return get_for_user_or_404(FooterPage.objects.all(), request, pk)


def _footerpage_steps(footer):
    """Stepper completeness для FooterPage: RU/KK/EN + соцсети."""
    ru_fields = ['intro_text_ru']
    kk_fields = ['intro_text_kk']
    en_fields = ['intro_text_en']
    socials_fields = ['facebook_url', 'instagram_url', 'threads_url', 'telegram_url']

    return [
        make_step(footer, id='ru', label='Текст (RU)', fields=ru_fields, required=True),
        make_step(footer, id='kk', label='Перевод KZ', fields=kk_fields),
        make_step(footer, id='en', label='Перевод EN', fields=en_fields),
        make_step(footer, id='socials', label='Соцсети', fields=socials_fields),
    ]


@never_cache
@backoffice_required
def content_footer_edit(request, pk):
    footer = _get_footer_for_user(request, pk)

    if request.method == 'POST':
        form = FooterPageEditForm(request.POST, instance=footer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Страница «Футер» сохранена.')
            return redirect('backoffice:content_footer_edit', pk=footer.pk)
    else:
        form = FooterPageEditForm(instance=footer)

    steps = _footerpage_steps(footer)

    return render_backoffice(
        request,
        'backoffice/content/footer/edit.html',
        active='footer',
        page_title=f'Футер — {footer.region.name}',
        context={
            'footer': footer,
            'form': form,
            'translation_langs': TRANSLATION_LANGS,
            'steps_json': json.dumps(steps),
            'translatable_bases_json': json.dumps(list(FOOTER_TRANSLATABLE)),
        },
    )


@require_POST
@backoffice_required
def content_footer_translate(request, pk):
    _get_footer_for_user(request, pk)
    return run_translate(request)
