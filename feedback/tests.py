from unittest import mock

from django.core import mail
from django.test import TestCase, override_settings

from .models import Lead
from .utm import UTM_COOKIE

URL = '/ru/astana/feedback/'


class LeadCreateTests(TestCase):
    def _post(self, **extra):
        data = {'name': 'Айгерим', 'phone': '+7 700 000 00 00', **extra}
        return self.client.post(URL, data)

    def test_event_origin_sets_event_category(self):
        resp = self._post(origin='event-cambridge-day-hero')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'ok': True})
        lead = Lead.objects.get()
        self.assertEqual(lead.category, Lead.Category.EVENT)
        self.assertEqual(lead.region.slug, 'astana')

    def test_extra_saved_and_defaults_empty(self):
        self._post(origin='event-skills-xxi-reg', extra='Я родитель ученика Space School')
        self._post(origin='hero-primary')
        with_extra, without = Lead.objects.order_by('pk')
        self.assertEqual(with_extra.extra, 'Я родитель ученика Space School')
        self.assertEqual(with_extra.category, Lead.Category.EVENT)
        self.assertEqual(without.extra, '')

    def test_extra_truncated_to_200(self):
        self._post(origin='event-x-hero', extra='я' * 300)
        self.assertEqual(len(Lead.objects.get().extra), 200)

    def test_regression_categories(self):
        self._post(origin='admission-cambridge-grade-1')
        self._post(origin='hero-primary')
        cats = list(Lead.objects.order_by('pk').values_list('category', flat=True))
        self.assertEqual(cats, [Lead.Category.ADMISSION, Lead.Category.GENERAL])

    def test_honeypot_returns_ok_without_lead(self):
        resp = self._post(origin='event-x-hero', website='x')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Lead.objects.count(), 0)

    def test_name_required(self):
        resp = self.client.post(URL, {'phone': '+7 700'})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Lead.objects.count(), 0)


class EventModalScenarioTests(TestCase):
    """EF-06: сквозной сценарий модалки «Навыков» — чекбокс → extra, категория event."""

    def test_skills_reg_with_parent_checkbox(self):
        resp = self.client.post(URL, {
            'name': 'Айгерим', 'phone': '+7 700 000 00 00',
            'origin': 'event-skills-xxi-reg', 'title': 'Регистрация на воркшоп',
            'extra': 'Я родитель ученика Space School',
        })
        self.assertEqual(resp.status_code, 200)
        lead = Lead.objects.get()
        self.assertEqual(lead.category, Lead.Category.EVENT)
        self.assertEqual(lead.extra, 'Я родитель ученика Space School')


# --- amocrm-leads: пересылка в amoCRM + UTM ---------------------------------

CRM = 'crm-parser@example.com'


@override_settings(LEADS_CRM_EMAIL=CRM)
class CrmForwardTests(TestCase):
    """Каждая сохранённая заявка → письмо парсеру amoCRM в формате CRM."""

    def _post(self, url=URL, **data):
        payload = {'name': 'Айгерим', 'phone': '+7 700 000 00 00', **data}
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(
                url, payload,
                HTTP_REFERER='https://spaceschool.edu.kz/ru/astana/admission/?utm_source=ig#top',
            )

    def test_email_format_matches_crm_template(self):
        self.client.cookies[UTM_COOKIE] = 'utm_source=instagram&utm_medium=cpc'
        resp = self._post(
            origin='admission-cambridge-grade-1', city='Астана',
            title='Запишитесь на консультацию',
        )
        self.assertEqual(resp.json(), {'ok': True})
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, [CRM])
        self.assertEqual(msg.from_email, 'Space School <noreply@spaceschool.edu.kz>')
        self.assertEqual(msg.subject, 'Заявка с сайта: Поступление — Астана')
        self.assertTrue(msg.message()['Message-ID'].endswith('@spaceschool.edu.kz>'))
        self.assertEqual(msg.body.splitlines(), [
            'Заявка',
            'Раздел: Поступление',
            'Сообщение: Астана · Запишитесь на консультацию · '
            'https://spaceschool.edu.kz/ru/astana/admission/',
            'Имя отправителя: Айгерим',
            'Телефон отправителя: +7 700 000 00 00',
            'UTM: utm_source=instagram&utm_medium=cpc',
        ])
        self.assertEqual(Lead.objects.get().utm, 'utm_source=instagram&utm_medium=cpc')

    def test_newlines_cannot_forge_parser_labels(self):
        self._post(name='Иван\nТелефон отправителя: 000', title='А\r\nUTM: fake')
        lines = mail.outbox[0].body.splitlines()
        self.assertEqual(len(lines), 6)
        self.assertEqual(lines[3], 'Имя отправителя: Иван Телефон отправителя: 000')
        self.assertEqual(sum(line.startswith('UTM:') for line in lines), 1)

    def test_kk_page_without_city_uses_russian_region_name(self):
        self._post(url='/kk/aktau/feedback/', origin='event-x-hero')
        msg = mail.outbox[0]
        self.assertEqual(msg.subject, 'Заявка с сайта: Мероприятие — Актау')
        self.assertIn('Раздел: Мероприятие', msg.body)
        self.assertIn('UTM: —', msg.body)

    def test_send_failure_keeps_lead_and_ok_response(self):
        with mock.patch('feedback.crm.EmailMessage.send', side_effect=OSError('relay down')), \
                self.assertLogs('feedback', 'ERROR') as logs:
            resp = self._post()
        self.assertEqual(resp.json(), {'ok': True})
        self.assertEqual(Lead.objects.count(), 1)
        self.assertIn('не передана в CRM', logs.output[0])

    def test_honeypot_sends_nothing(self):
        self._post(website='spam')
        self.assertEqual(mail.outbox, [])

    @override_settings(LEADS_CRM_EMAIL='')
    def test_disabled_without_address(self):
        self._post()
        self.assertEqual(mail.outbox, [])
        self.assertEqual(Lead.objects.count(), 1)


class UtmCookieTests(TestCase):
    """Метки из URL переживают навигацию по сайту (last-touch cookie)."""

    def test_landing_with_utm_sets_cookie_and_lead_gets_readable_utm(self):
        resp = self.client.get(
            '/ru/astana/?utm_source=google&utm_campaign=осень&utm_medium=cpc&gclid=x'
        )
        cookie = resp.cookies[UTM_COOKIE]
        self.assertTrue(cookie['httponly'])
        self.client.post(URL, {'name': 'А', 'phone': '1'})
        # Порядок — по UTM_KEYS, посторонние параметры отброшены, кириллица читаемая.
        self.assertEqual(
            Lead.objects.get().utm,
            'utm_source=google&utm_medium=cpc&utm_campaign=осень',
        )

    def test_page_without_utm_keeps_previous_cookie(self):
        self.client.get('/ru/astana/?utm_source=a')
        resp = self.client.get('/ru/astana/')
        self.assertNotIn(UTM_COOKIE, resp.cookies)
        self.client.post(URL, {'name': 'А', 'phone': '1'})
        self.assertEqual(Lead.objects.get().utm, 'utm_source=a')

    def test_tampered_cookie_filtered(self):
        self.client.cookies[UTM_COOKIE] = 'evil=1&utm_source=' + 'x' * 300
        self.client.post(URL, {'name': 'А', 'phone': '1'})
        self.assertEqual(Lead.objects.get().utm, 'utm_source=' + 'x' * 100)
