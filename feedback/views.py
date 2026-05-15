"""POST-эндпоинт приёма заявок из модалки `partials/modals/feedback.html`.

Запросы идут с CSRF-токеном (рендерится `{% csrf_token %}` внутри формы).
Ответ — JSON `{ok: true}` / `{ok: false, error: ...}` — Alpine переключает
форму в success-state или показывает текст ошибки.
"""
from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST

from .models import Lead


# Honeypot: невидимое поле name="website". Боты заполняют любые поля,
# люди не видят. Если пришло непустое — молча отвечаем 200 ok=true и
# ничего не пишем — спам-бот думает что прокатило, не повторяет.
HONEYPOT_FIELD = 'website'

MAX_FIELD_LEN = {
    'name': 120,
    'phone': 40,
    'city': 80,
    'origin': 120,
    'title': 200,
}


def _client_ip(request) -> str | None:
    # X-Forwarded-For — за nginx первое значение в списке.
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') or None


@method_decorator(require_POST, name='dispatch')
class LeadCreateView(View):
    """Приём заявки. Region берётся из `request.region` (URL-prefix)."""

    def post(self, request, *args, **kwargs):
        # Honeypot: бот заполнил скрытое поле → имитируем успех.
        if request.POST.get(HONEYPOT_FIELD, '').strip():
            return JsonResponse({'ok': True})

        region = getattr(request, 'region', None)
        if region is None:
            return JsonResponse(
                {'ok': False, 'error': 'region_required'},
                status=400,
            )

        name = (request.POST.get('name') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        if not name or not phone:
            return JsonResponse(
                {'ok': False, 'error': 'name_and_phone_required'},
                status=400,
            )

        data = {
            'name': name[:MAX_FIELD_LEN['name']],
            'phone': phone[:MAX_FIELD_LEN['phone']],
            'city': (request.POST.get('city') or '').strip()[:MAX_FIELD_LEN['city']],
            'origin': (request.POST.get('origin') or '').strip()[:MAX_FIELD_LEN['origin']],
            'title': (request.POST.get('title') or '').strip()[:MAX_FIELD_LEN['title']],
        }

        Lead.objects.create(
            region=region,
            ip_address=_client_ip(request),
            user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:300],
            policy_version=getattr(settings, 'PRIVACY_POLICY_VERSION', 'v1'),
            **data,
        )
        return JsonResponse({'ok': True})
