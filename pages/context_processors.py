from .models import ContactsPage


SOCIAL_KEYS = ('instagram', 'facebook', 'threads', 'telegram')


def socials(request):
    """Соцсети текущего региона для рендера в footer.

    Берёт URL'ы из ContactsPage.{facebook,instagram,threads,telegram}_url.
    Если регион не определён или у него нет ContactsPage — возвращает
    пустой dict (шаблон через {% if %} скроет иконки).
    """
    region = getattr(request, 'region', None)
    if region is None:
        return {'socials': {}}

    page = (
        ContactsPage.objects
        .filter(region=region)
        .only(*[f'{k}_url' for k in SOCIAL_KEYS])
        .first()
    )
    if page is None:
        return {'socials': {}}

    return {
        'socials': {k: getattr(page, f'{k}_url') for k in SOCIAL_KEYS},
    }
