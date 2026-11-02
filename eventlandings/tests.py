from collections import namedtuple
from datetime import date, datetime, time, timedelta
from io import BytesIO
from unittest import mock
from zoneinfo import ZoneInfo

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from PIL import Image

from core.gallery import strict_zip_arrange
from pages.models import HomeGalleryImage, HomePage
from regions.models import Region
from team.models import TeamMember

from .models import (
    EventLanding,
    EventLandingDay,
    EventLandingGalleryImage,
    EventLandingMaterial,
    EventLandingProgramRow,
    EventLandingTile,
)

ALMATY = ZoneInfo('Asia/Almaty')


def _png(w, h):
    buf = BytesIO()
    Image.new('RGB', (w, h), 'white').save(buf, 'PNG')
    return SimpleUploadedFile(f'{w}x{h}.png', buf.getvalue(), content_type='image/png')


class EventLandingModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.astana = Region.objects.get(slug='astana')
        cls.aktau = Region.objects.get(slug='aktau')

    def _landing(self, slug='test-event', region=None):
        return EventLanding.objects.create(region=region or self.astana, slug=slug, title='Test')

    def test_is_past_without_days(self):
        landing = self._landing()
        self.assertIsNone(landing.starts_at)
        self.assertIsNone(landing.ends_at)
        self.assertFalse(landing.is_past)

    def test_is_past_tomorrow_and_yesterday(self):
        today = timezone.localdate()
        future = self._landing('future')
        EventLandingDay.objects.create(
            landing=future, date=today + timedelta(days=1), start=time(10), end=time(12))
        past = self._landing('past')
        EventLandingDay.objects.create(
            landing=past, date=today - timedelta(days=1), start=time(10), end=time(12))
        self.assertFalse(future.is_past)
        self.assertTrue(past.is_past)

    def test_is_past_boundary_almaty(self):
        landing = self._landing()
        EventLandingDay.objects.create(
            landing=landing, date=date(2026, 11, 14), start=time(11), end=time(14))
        # 13:59 по Алматы — ещё идёт; 14:01 — прошло.
        before = datetime(2026, 11, 14, 13, 59, tzinfo=ALMATY)
        after = datetime(2026, 11, 14, 14, 1, tzinfo=ALMATY)
        with mock.patch('django.utils.timezone.now', return_value=before):
            self.assertFalse(landing.is_past)
        with mock.patch('django.utils.timezone.now', return_value=after):
            self.assertTrue(landing.is_past)

    def test_starts_ends_aware_two_days(self):
        landing = self._landing()
        EventLandingDay.objects.create(
            landing=landing, date=date(2026, 11, 22), start=time(9, 30), end=time(17))
        EventLandingDay.objects.create(
            landing=landing, date=date(2026, 11, 21), start=time(9, 30), end=time(17))
        self.assertTrue(timezone.is_aware(landing.starts_at))
        self.assertEqual(landing.starts_at, datetime(2026, 11, 21, 9, 30, tzinfo=ALMATY))
        self.assertEqual(landing.ends_at, datetime(2026, 11, 22, 17, 0, tzinfo=ALMATY))
        self.assertEqual(str(landing.starts_at.tzinfo), 'Asia/Almaty')

    def test_unique_slug_per_region(self):
        self._landing('same', self.astana)
        self._landing('same', self.aktau)  # другой регион — ок
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._landing('same', self.astana)

    def test_price_display(self):
        landing = EventLanding(region=self.astana, slug='p', title='P', price=18990)
        self.assertEqual(landing.price_display, '18\xa0990\xa0₸')
        landing.price = None
        self.assertEqual(landing.price_display, '')


class StrictZipArrangeTests(TestCase):
    def test_order_wide_tall_square(self):
        Img = namedtuple('Img', 'order pk orientation')
        imgs = [
            Img(0, 1, 'wide'), Img(0, 2, 'wide'), Img(0, 3, 'square'),
            Img(0, 4, 'tall'), Img(0, 5, 'wide'), Img(0, 6, 'tall'),
        ]
        result = [i.orientation for i in strict_zip_arrange(imgs)]
        self.assertEqual(result, ['wide', 'tall', 'wide', 'tall', 'wide', 'square'])


class HomeGalleryOrientationTests(TestCase):
    def test_auto_orientation_after_refactor(self):
        home = HomePage.objects.filter(region__slug='astana').first()
        if home is None:
            home = HomePage.objects.create(region=Region.objects.get(slug='astana'))
        wide = HomeGalleryImage.objects.create(home_page=home, image=_png(400, 200))
        tall = HomeGalleryImage.objects.create(home_page=home, image=_png(200, 400))
        self.assertEqual(wide.orientation, 'wide')
        self.assertEqual(tall.orientation, 'tall')
        for img in (wide, tall):
            img.image.delete(save=False)


class SeedNovember2026Tests(TestCase):
    """Data-миграция 0002 выполняется и в тестовой БД — проверяем результат."""

    def _get(self, slug):
        return EventLanding.objects.get(region__slug='astana', slug=slug)

    def test_three_landings_publish_flags(self):
        slugs = set(EventLanding.objects.filter(region__slug='astana').values_list('slug', flat=True))
        self.assertEqual(slugs, {'cambridge-day', 'skills-xxi', 'cambridge-programme-leader'})
        self.assertTrue(self._get('cambridge-day').is_published)
        self.assertTrue(self._get('cambridge-programme-leader').is_published)
        self.assertFalse(self._get('skills-xxi').is_published)

    def test_day_content(self):
        day = self._get('cambridge-day')
        days = list(day.days.all())
        self.assertEqual(len(days), 1)
        self.assertEqual((days[0].date, days[0].start, days[0].end),
                         (date(2026, 11, 14), time(11), time(14)))
        rows = list(days[0].rows.all())
        self.assertEqual(len(rows), 8)
        self.assertTrue(day.lead.startswith('Cambridge Day — день открытых дверей'))
        self.assertEqual(rows[0].start, time(11))
        self.assertEqual(rows[0].duration_min, 20)

    def test_skills_and_leader_content(self):
        skills = self._get('skills-xxi')
        rows = EventLandingProgramRow.objects.filter(day__landing=skills)
        self.assertEqual(rows.count(), 9)
        self.assertEqual(rows.filter(is_break=True).count(), 1)

        leader = self._get('cambridge-programme-leader')
        self.assertEqual(leader.days.count(), 2)
        self.assertEqual(EventLandingProgramRow.objects.filter(day__landing=leader).count(), 20)
        self.assertEqual(leader.materials.count(), 7)
        self.assertEqual(leader.tiles.count(), 2)
        self.assertEqual(leader.price_display, '50\xa0000\xa0₸')
        module1 = EventLandingProgramRow.objects.get(
            day__landing=leader, start=time(9, 50))
        self.assertEqual(module1.duration_min, 80)

    def test_forward_idempotent(self):
        import importlib

        from django.apps import apps as global_apps
        mod = importlib.import_module('eventlandings.migrations.0002_seed_november_2026')
        before = (EventLanding.objects.count(), EventLandingProgramRow.objects.count(),
                  EventLandingMaterial.objects.count(), EventLandingTile.objects.count())
        mod.forward(global_apps, None)
        after = (EventLanding.objects.count(), EventLandingProgramRow.objects.count(),
                 EventLandingMaterial.objects.count(), EventLandingTile.objects.count())
        self.assertEqual(before, after)

    def test_aktau_has_no_landings(self):
        self.assertEqual(EventLanding.objects.filter(region__slug='aktau').count(), 0)


class LandingDetailViewTests(TestCase):
    """EF-05: лендинг события (данные — миграция 0002)."""

    DAY = '/ru/astana/event/cambridge-day/'

    @classmethod
    def setUpTestData(cls):
        cls.astana = Region.objects.get(slug='astana')
        HomePage.objects.get_or_create(region=cls.astana)
        cls.day = EventLanding.objects.get(region=cls.astana, slug='cambridge-day')
        cls.skills = EventLanding.objects.get(region=cls.astana, slug='skills-xxi')
        cls.leader = EventLanding.objects.get(region=cls.astana, slug='cambridge-programme-leader')

    def _now(self):
        # До всех событий — чтобы «прошло» не зависело от даты прогона тестов.
        return mock.patch('django.utils.timezone.now',
                          return_value=datetime(2026, 11, 1, 12, 0, tzinfo=ALMATY))

    def test_day_renders_ctas(self):
        with self._now():
            resp = self.client.get(self.DAY)
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertRegex(html, r'<h1[^>]*>Cambridge Day</h1>')
        for place in ('hero', 'reg', 'sticky', 'consult'):
            self.assertIn(f'data-feedback-origin="event-cambridge-day-{place}"', html)
        self.assertNotIn('data-feedback-price', html)

    def test_draft_404_then_published(self):
        url = '/ru/astana/event/skills-xxi/'
        with self._now():
            self.assertEqual(self.client.get(url).status_code, 404)
            EventLanding.objects.filter(pk=self.skills.pk).update(is_published=True)
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn('data-feedback-parent-checkbox="1"', html)
        self.assertRegex(html, 'data-feedback-price="18\xa0990')

    def test_other_region_404_and_kk_fallback(self):
        with self._now():
            self.assertEqual(self.client.get('/ru/aktau/event/cambridge-day/').status_code, 404)
            resp = self.client.get('/kk/astana/event/cambridge-day/')
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn('<html lang="kk">', html)
        self.assertRegex(html, r'<h1[^>]*>Cambridge Day</h1>')

    def test_upcoming(self):
        with self._now():
            day_ctx = self.client.get(self.DAY).context
            leader_ctx = self.client.get('/ru/astana/event/cambridge-programme-leader/').context
        self.assertEqual([lnd.slug for lnd in day_ctx['upcoming']], ['cambridge-programme-leader'])
        self.assertEqual([lnd.slug for lnd in leader_ctx['upcoming']], ['cambridge-day'])

    def test_gallery_fallback_to_home(self):
        home = HomePage.objects.get(region=self.astana)
        imgs = [HomeGalleryImage.objects.create(home_page=home, image=_png(400, 200)),
                HomeGalleryImage.objects.create(home_page=home, image=_png(200, 400))]
        try:
            with self._now():
                ctx = self.client.get(self.DAY).context
            self.assertEqual(ctx['gallery'], strict_zip_arrange(home.gallery.all()))
            own = EventLandingGalleryImage.objects.create(landing=self.day, image=_png(300, 300))
            imgs.append(own)
            with self._now():
                ctx = self.client.get(self.DAY).context
            self.assertEqual(ctx['gallery'], [own])
        finally:
            for img in imgs:
                img.image.delete(save=False)

    def test_leaders_placeholder_and_published_only(self):
        self.day.leaders.clear()
        with self._now():
            html = self.client.get(self.DAY).content.decode()
        self.assertIn('Ведущий будет объявлен', html)
        shown = TeamMember.objects.create(region=self.astana, slug='ef-shown', name='Тест Показан',
                                          is_published=True)
        hidden = TeamMember.objects.create(region=self.astana, slug='ef-hidden', name='Тест Скрыт',
                                           is_published=False)
        self.day.leaders.set([shown, hidden])
        with self._now():
            html = self.client.get(self.DAY).content.decode()
        self.assertIn('Тест Показан', html)
        self.assertNotIn('Тест Скрыт', html)
        self.assertNotIn('Ведущий будет объявлен', html)


class FeedbackSectionRegressionTests(TestCase):
    def test_default_texts_and_origin(self):
        from django.template.loader import render_to_string
        from django.utils.translation import override
        with override('ru'):
            html = render_to_string('partials/feedback_section.html', {'origin': 'home'})
        self.assertIn('Готовы запустить', html)
        self.assertIn('data-feedback-origin="home-primary"', html)
        self.assertIn('data-feedback-origin="home-city"', html)
