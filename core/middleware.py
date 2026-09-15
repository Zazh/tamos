"""Middleware уровня проекта."""
from django.conf import settings
from django.utils import translation


class StaffLanguageMiddleware:
    """Фиксирует русский язык на staff-интерфейсах (`/backoffice/`, `/admin/`).

    Зачем
    -----
    Оба пути лежат ВНЕ `i18n_patterns` (см. `core/urls.py`), языкового префикса в URL
    нет — поэтому `LocaleMiddleware` брал язык из cookie `django_language`. А её
    пишет `LanguageCookieMiddleware` по последней странице публичного сайта: зашёл
    менеджер на `/` → редирект на `/kk/` → cookie `kk` → бэкофис открывается
    по-казахски.

    Интерфейс сотрудников — всегда русский, это осознанное решение: 320
    `verbose_name`/`help_text` в моделях и ~137 лейблов в шаблонах бэкофиса
    захардкожены по-русски (не обёрнуты в gettext). Под `kk` получался гибрид:
    казахская «обвязка» + русские подписи полей.

    Важно: язык здесь **не** пишется в cookie — `LanguageCookieMiddleware`
    пропускает такие запросы по флагу `request.is_staff_ui`, иначе визит в
    бэкофис молча переключал бы публичный сайт менеджера на русский.

    Языковые табы RU/KK/EN внутри бэкофиса — это язык РЕДАКТИРУЕМОГО КОНТЕНТА
    (modeltranslation), к языку интерфейса отношения не имеют.
    """

    LANGUAGE = 'ru'

    def __init__(self, get_response):
        self.get_response = get_response
        self.prefixes = ('/backoffice/', '/' + settings.ADMIN_URL.lstrip('/'))

    def __call__(self, request):
        request.is_staff_ui = request.path.startswith(self.prefixes)
        if request.is_staff_ui:
            # Не деактивируем на выходе: LocaleMiddleware активирует язык на
            # каждом запросе заново, а его process_response читает активный
            # язык для заголовка Content-Language.
            translation.activate(self.LANGUAGE)
            request.LANGUAGE_CODE = self.LANGUAGE
        return self.get_response(request)
