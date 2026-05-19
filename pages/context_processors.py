from .models import FooterPage


SOCIAL_KEYS = ('instagram', 'facebook', 'threads', 'telegram')


def footer(request):
    """Контент футера для текущего региона.

    Возвращает:
      footer.intro_text  — короткий параграф под лого
      footer.socials     — dict {instagram, facebook, threads, telegram} с URL'ами

    Если регион не определён или FooterPage отсутствует — отдаём пустой объект,
    шаблон через {% if %} скроет блоки.

    До миграции pages/0025 эти данные жили на ContactsPage; теперь — отдельный
    раздел backoffice «Футер».
    """
    region = getattr(request, 'region', None)
    if region is None:
        return {'footer': {'intro_text': '', 'socials': {}}}

    page = (
        FooterPage.objects
        .filter(region=region)
        .only('intro_text', *[f'{k}_url' for k in SOCIAL_KEYS])
        .first()
    )
    if page is None:
        return {'footer': {'intro_text': '', 'socials': {}}}

    return {
        'footer': {
            'intro_text': page.intro_text or '',
            'socials': {k: getattr(page, f'{k}_url') for k in SOCIAL_KEYS},
        },
    }
