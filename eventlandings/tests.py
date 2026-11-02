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

from .models import EventLanding, EventLandingDay

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
