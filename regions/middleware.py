from django.conf import settings
from django.http import Http404


class LanguageCookieMiddleware:
    """
    Синхронизирует cookie `django_language` с активным языком (URL-префикс).

    Зачем: language switcher в `partials/header.html` — обычные `<a href="/ru/...">`,
    не POST в `/i18n/setlang/`, поэтому Django сам cookie не ставит. Без синка
    `root_redirect` (см. `core/views.py`) при следующем визите на `/` не знает
    о выборе юзера и всегда отправляет на `kk` (default по compliance).

    LocaleMiddleware ставит `request.LANGUAGE_CODE` из URL — берём его как
    источник истины и пишем cookie на 1 год (как `region`-cookie у соседа).
    """

    COOKIE_MAX_AGE = 60 * 60 * 24 * 365

    def __init__(self, get_response):
        self.get_response = get_response
        self._allowed = {code for code, _ in settings.LANGUAGES}

    def __call__(self, request):
        response = self.get_response(request)
        lang = getattr(request, 'LANGUAGE_CODE', None)
        if lang in self._allowed and request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME) != lang:
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                lang,
                max_age=settings.LANGUAGE_COOKIE_AGE or self.COOKIE_MAX_AGE,
                samesite='Lax',
            )
        return response


class RegionMiddleware:
    """
    Парсит `region_slug` из URL kwargs (захватываются в i18n_patterns), резолвит
    в объект Region и кладёт в `request.region`. Сохраняет последний выбор в cookie,
    чтобы корневой URL `/` мог отредиректить пользователя в его регион.

    URL-паттерн должен называть kwarg именно `region_slug` — иначе middleware
    его не увидит.
    """
    COOKIE_NAME = 'region'
    COOKIE_MAX_AGE = 60 * 60 * 24 * 365

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.region = None
        request._set_region_cookie = None
        response = self.get_response(request)
        if request._set_region_cookie:
            response.set_cookie(
                self.COOKIE_NAME,
                request._set_region_cookie,
                max_age=self.COOKIE_MAX_AGE,
                samesite='Lax',
            )
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Не делаем .pop() — это тот же dict, что и request.resolver_match.kwargs,
        # а switch_language_url читает оттуда, чтобы построить URL под другим языком.
        slug = view_kwargs.get('region_slug')
        if slug is None:
            return None
        from .models import Region
        try:
            region = Region.objects.get(slug=slug, is_active=True)
        except Region.DoesNotExist as exc:
            raise Http404(f"Unknown or inactive region '{slug}'") from exc
        request.region = region
        if request.COOKIES.get(self.COOKIE_NAME) != slug:
            request._set_region_cookie = slug
        return None
