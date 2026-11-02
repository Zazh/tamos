from django.test import TestCase

from .models import Lead

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
