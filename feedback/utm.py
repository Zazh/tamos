"""UTM-метки заявок (бриф `amocrm-leads`, Р-6): last-touch через cookie.

Посетитель приходит по рекламной ссылке `…?utm_source=…`, гуляет по сайту и
оставляет заявку на другой странице — метки к этому моменту из URL пропали.
Поэтому middleware при любом GET с `utm_*` кладёт их в cookie на 30 дней
(новый заход с метками перезаписывает — last-touch), а `LeadCreateView`
читает cookie и пишет метки в `Lead.utm` и в письмо для CRM.
"""
from urllib.parse import parse_qsl, urlencode

UTM_COOKIE = 'ss_utm'
UTM_KEYS = ('utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term')
UTM_MAX_AGE = 60 * 60 * 24 * 30
UTM_VALUE_MAX_LEN = 100
UTM_MAX_LEN = 500  # = Lead.utm.max_length


def _pairs(mapping) -> list[tuple[str, str]]:
    pairs = []
    for key in UTM_KEYS:
        value = ' '.join((mapping.get(key) or '').split())[:UTM_VALUE_MAX_LEN]
        if value:
            pairs.append((key, value))
    return pairs


def utm_from_cookie(raw: str) -> str:
    """Человекочитаемая строка `utm_source=ig&utm_campaign=осень` для Lead/CRM.

    Cookie приходит от клиента — заново фильтруем ключи и длины.
    """
    if not raw:
        return ''
    pairs = _pairs(dict(parse_qsl(raw)))
    return '&'.join(f'{k}={v}' for k, v in pairs)[:UTM_MAX_LEN]


class UtmCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.method == 'GET':
            pairs = _pairs(request.GET)
            if pairs:
                # urlencode: значение cookie — только ASCII (кириллица в метках бывает).
                response.set_cookie(
                    UTM_COOKIE,
                    urlencode(pairs),
                    max_age=UTM_MAX_AGE,
                    samesite='Lax',
                    httponly=True,
                    secure=request.is_secure(),
                )
        return response
