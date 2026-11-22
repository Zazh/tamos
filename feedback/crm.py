"""Пересылка заявки в amoCRM — письмом на адрес почтового парсера CRM.

Формат задан CRM (бриф `amocrm-leads`): plain text, метки по одной на строку —
парсер вытаскивает значения по меткам. Адрес — `settings.LEADS_CRM_EMAIL`
(пусто = пересылка выключена: дев, тесты). Письмо уходит через relay
`mailrelay` из compose; он сам доставляет на MX amoCRM и держит очередь.

Источник правды — наша БД: письмо отправляется ПОСЛЕ сохранения Lead, сбой
отправки только логируется и не ломает ответ посетителю.
"""
import logging
import re
from email.utils import make_msgid, parseaddr
from urllib.parse import urlsplit

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import translation

logger = logging.getLogger(__name__)

_WHITESPACE = re.compile(r'\s+')
PAGE_URL_MAX_LEN = 300


def _one_line(value) -> str:
    # Любые переносы/табы → пробел: значение посетителя не может начать
    # новую строку и подделать метку парсера («Телефон отправителя: …»).
    return _WHITESPACE.sub(' ', str(value or '')).strip()


def page_url_from_referer(referer: str) -> str:
    """Страница, с которой отправили форму, без query (UTM идут своей строкой)."""
    if not referer:
        return ''
    parts = urlsplit(referer)
    return parts._replace(query='', fragment='').geturl()[:PAGE_URL_MAX_LEN]


def build_message(lead, page_url: str = '') -> tuple[str, str]:
    """(subject, body) письма для парсера amoCRM."""
    # Письмо читают менеджеры CRM — названия по-русски при любом языке страницы.
    with translation.override('ru'):
        section = lead.get_category_display()
        city = _one_line(lead.city) or lead.region.name
    message = ' · '.join(filter(None, (
        city,
        _one_line(lead.title),
        _one_line(lead.extra),
        _one_line(page_url),
    )))
    body = '\n'.join((
        'Заявка',
        f'Раздел: {section}',
        f'Сообщение: {message}',
        f'Имя отправителя: {_one_line(lead.name)}',
        f'Телефон отправителя: {_one_line(lead.phone)}',
        f'UTM: {_one_line(lead.utm) or "—"}',
    )) + '\n'
    subject = f'Заявка с сайта: {section} — {city}'
    return subject, body


def forward_lead(lead, page_url: str = '') -> None:
    """Отправить заявку на парсер amoCRM. Никогда не бросает исключений."""
    recipient = settings.LEADS_CRM_EMAIL
    if not recipient:
        return
    try:
        subject, body = build_message(lead, page_url)
        sender = settings.DEFAULT_FROM_EMAIL
        # Message-ID на домене отправителя, а не на имени контейнера (спам-фильтры за это штрафуют).
        domain = parseaddr(sender)[1].rpartition('@')[2]
        EmailMessage(
            subject, body, sender, [recipient],
            headers={'Message-ID': make_msgid(domain=domain)},
        ).send()
    except Exception:
        logger.exception('Заявка #%s не передана в CRM', lead.pk)
        return
    logger.info('Заявка #%s передана в CRM', lead.pk)
