from datetime import datetime, timedelta
from unittest import mock
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.utils import timezone

from eventlandings.models import EventLanding, EventLandingDay
from regions.models import Region

from .models import Event

ALMATY = ZoneInfo('Asia/Almaty')
NOW = datetime(2026, 11, 1, 12, 0, tzinfo=ALMATY)


class MixedFeedTests(TestCase):
    """EF-07: /events/ — новости (seed events/0002) + лендинги (EF-04) одной лентой."""

    def _get(self, url='/ru/astana/events/'):
        with mock.patch('django.utils.timezone.now', return_value=NOW):
            return self.client.get(url)

    def test_astana_mixed_sorted_desc(self):
        resp = self._get()
        self.assertEqual(resp.status_code, 200)
        items = list(resp.context['items'])
        kinds = [i.kind for i in items]
        self.assertIn('landing', kinds)
        self.assertIn('news', kinds)
        slugs = [i.obj.slug for i in items if i.kind == 'landing']
        self.assertNotIn('skills-xxi', slugs)  # черновик
        self.assertEqual(slugs[:2], ['cambridge-programme-leader', 'cambridge-day'])
        dts = [i.sort_dt for i in items]
        self.assertEqual(dts, sorted(dts, reverse=True))
        html = resp.content.decode()
        self.assertIn('href="/ru/astana/event/cambridge-day/" class="article-card__link"', html)
        self.assertNotIn('program-card--event', html)  # лендинг — базовой карточкой, без цены
        self.assertNotIn('50\xa0000', html)

    def test_aktau_only_news(self):
        items = list(self._get('/ru/aktau/events/').context['items'])
        self.assertTrue(items)
        self.assertEqual({i.kind for i in items}, {'news'})

    def test_landing_without_days_hidden(self):
        astana = Region.objects.get(slug='astana')
        EventLanding.objects.create(region=astana, slug='no-days', title='Без дней', is_published=True)
        slugs = [i.obj.slug for i in self._get().context['items'] if i.kind == 'landing']
        self.assertNotIn('no-days', slugs)

    def test_past_badge(self):
        with mock.patch('django.utils.timezone.now',
                        return_value=datetime(2026, 11, 15, 12, 0, tzinfo=ALMATY)):
            html = self.client.get('/ru/astana/events/').content.decode()
        self.assertIn('Состоялось', html)

    def test_pagination(self):
        astana = Region.objects.get(slug='astana')
        base = timezone.now() - timedelta(days=400)
        for n in range(10):
            Event.objects.create(region=astana, slug=f'ef07-{n}', title=f'N{n}', content='x',
                                 published_at=base + timedelta(days=n))
        resp = self._get()
        self.assertTrue(resp.context['page_obj'].has_next())
        self.assertEqual(self._get('/ru/astana/events/?page=2').status_code, 200)
