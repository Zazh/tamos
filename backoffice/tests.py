import json
import re
import shutil
import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.models import User
from eventlandings.models import (
    EventLanding,
    EventLandingDay,
    EventLandingGalleryImage,
    EventLandingMaterial,
    EventLandingTile,
)
from regions.models import Region
from team.models import TeamMember

from .forms import (
    EventLandingDayFormSet,
    EventLandingEditForm,
    EventLandingMaterialFormSet,
    EventLandingProgramRowFormSet,
    EventLandingTileFormSet,
)


def _form_to_data(form):
    """POST-данные из unbound-формы: текущие значения полей под их html-именами."""
    data = {}
    for name in form.fields:
        bf = form[name]
        value = bf.value()
        if value is None or value is False:
            continue
        if value is True:
            data[bf.html_name] = 'on'
        elif isinstance(value, (list, tuple)):
            data[bf.html_name] = [str(v) for v in value]
        else:
            data[bf.html_name] = str(value)
    return data


def _formset_to_data(formset):
    data = _form_to_data(formset.management_form)
    for form in formset.forms:
        data.update(_form_to_data(form))
    return data


def _png(w, h):
    buf = BytesIO()
    Image.new('RGB', (w, h), 'white').save(buf, 'PNG')
    return SimpleUploadedFile(f'{w}x{h}.png', buf.getvalue(), content_type='image/png')


def _edit_data(landing, user):
    """POST основной формы мероприятия + трёх inline-formset'ов как есть."""
    data = _form_to_data(EventLandingEditForm(instance=landing, user=user))
    data.update(_formset_to_data(EventLandingDayFormSet(instance=landing, prefix='days')))
    data.update(_formset_to_data(EventLandingMaterialFormSet(instance=landing, prefix='materials')))
    data.update(_formset_to_data(EventLandingTileFormSet(instance=landing, prefix='tiles')))
    return data


class BackofficeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.astana = Region.objects.get(slug='astana')
        cls.aktau = Region.objects.get(slug='aktau')
        cls.superuser = User.objects.create_superuser('su', 'su@example.com', 'pass')
        cls.manager_aktau = User.objects.create_user(
            'manager-aktau', password='pass', is_staff=True, manager_region=cls.aktau)

    def setUp(self):
        self.client.force_login(self.superuser)


class EventLandingSectionTests(BackofficeTestCase):
    """EF-10: раздел «Мероприятия» — список, lazy-create, edit, translate."""

    def setUp(self):
        super().setUp()
        self.day = EventLanding.objects.get(region=self.astana, slug='cambridge-day')

    def _edit_url(self, landing):
        return reverse('backoffice:content_eventlandings_edit', kwargs={'pk': landing.pk})

    def _post_edit(self, landing, **overrides):
        data = _edit_data(landing, self.superuser)
        for key, value in overrides.items():
            if value is None:
                data.pop(key, None)
            else:
                data[key] = value
        return self.client.post(self._edit_url(landing), data)

    def test_list_superuser_sees_astana_landings(self):
        resp = self.client.get(reverse('backoffice:content_eventlandings_list'))
        self.assertEqual(resp.status_code, 200)
        slugs = {lp.slug for lp in resp.context['page'].object_list}
        self.assertEqual(slugs, {'cambridge-day', 'skills-xxi', 'cambridge-programme-leader'})

    def test_create_makes_draft_in_default_region(self):
        resp = self.client.post(reverse('backoffice:content_eventlandings_create'))
        landing = EventLanding.objects.latest('pk')
        self.assertRedirects(resp, self._edit_url(landing), fetch_redirect_response=False)
        self.assertTrue(landing.slug.startswith('draft-'))
        self.assertEqual(landing.region, Region.objects.get(is_default=True))
        self.assertFalse(landing.is_published)

    def test_first_title_turns_draft_slug_readable(self):
        self.client.post(reverse('backoffice:content_eventlandings_create'))
        landing = EventLanding.objects.latest('pk')
        resp = self._post_edit(landing, title_ru='Тест')
        self.assertRedirects(resp, self._edit_url(landing), fetch_redirect_response=False)
        landing.refresh_from_db()
        self.assertRegex(landing.slug, r'^test-[0-9a-f]{4}$')
        # Второе сохранение slug не трогает.
        self._post_edit(landing, title_ru='Другое название')
        slug = landing.slug
        landing.refresh_from_db()
        self.assertEqual(landing.slug, slug)

    def test_paid_price_saved(self):
        resp = self._post_edit(self.day, is_paid='on', price='1000')
        self.assertEqual(resp.status_code, 302)
        self.day.refresh_from_db()
        self.assertTrue(self.day.is_paid)
        self.assertEqual(self.day.price, 1000)

    def test_paid_without_price_is_error(self):
        resp = self._post_edit(self.day, is_paid='on', price=None)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('price', resp.context['form'].errors)
        self.day.refresh_from_db()
        self.assertFalse(self.day.is_paid)

    def test_free_event_drops_parent_checkbox(self):
        self._post_edit(self.day, show_parent_checkbox='on')
        self.day.refresh_from_db()
        self.assertFalse(self.day.show_parent_checkbox)

    def test_publish_without_title_is_error_on_top(self):
        resp = self._post_edit(self.day, title_ru='', is_published='on')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['form'].non_field_errors())
        self.assertContains(resp, 'заполните заголовок на русском')
        self.day.refresh_from_db()
        self.assertEqual(self.day.title_ru, 'Cambridge Day')

    def test_slug_and_region_not_editable_via_post(self):
        self._post_edit(self.day, slug='hacked', region=str(self.aktau.pk))
        self.day.refresh_from_db()
        self.assertEqual((self.day.slug, self.day.region_id), ('cambridge-day', self.astana.pk))

    def test_leader_from_other_region_rejected(self):
        stranger = TeamMember.objects.create(
            region=self.aktau, slug='stranger', name='Чужой', role='Педагог', is_published=True)
        before = set(self.day.leaders.values_list('pk', flat=True))
        resp = self._post_edit(self.day, leaders=[str(stranger.pk)])
        self.assertEqual(resp.status_code, 200)
        self.assertIn('leaders', resp.context['form'].errors)
        self.assertEqual(set(self.day.leaders.values_list('pk', flat=True)), before)

    def test_leaders_saved(self):
        member = TeamMember.objects.create(
            region=self.astana, slug='ef10-leader', name='Ведущий', role='Педагог', is_published=True)
        self._post_edit(self.day, leaders=[str(member.pk)])
        self.assertEqual(list(self.day.leaders.all()), [member])

    @override_settings(GEMINI_API_KEY='')
    def test_translate_without_key_is_503_json(self):
        resp = self.client.post(
            reverse('backoffice:content_eventlandings_translate', kwargs={'pk': self.day.pk}),
            data='{"by_lang": {"kk": {"title_kk": "Cambridge Day"}}}',
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 503)
        self.assertIn('error', resp.json())

    def test_delete(self):
        resp = self.client.post(
            reverse('backoffice:content_eventlandings_delete', kwargs={'pk': self.day.pk}))
        self.assertRedirects(
            resp, reverse('backoffice:content_eventlandings_list'), fetch_redirect_response=False)
        self.assertFalse(EventLanding.objects.filter(pk=self.day.pk).exists())

    def test_manager_of_other_region_gets_404(self):
        self.client.force_login(self.manager_aktau)
        resp = self.client.get(reverse('backoffice:content_eventlandings_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(resp.context['page'].object_list), [])
        pk = {'pk': self.day.pk}
        self.assertEqual(self.client.get(self._edit_url(self.day)).status_code, 404)
        for name in ('translate', 'seo', 'delete'):
            url = reverse(f'backoffice:content_eventlandings_{name}', kwargs=pk)
            self.assertEqual(self.client.post(url).status_code, 404, name)
        self.assertTrue(EventLanding.objects.filter(pk=self.day.pk).exists())

    def test_manager_creates_in_own_region(self):
        self.client.force_login(self.manager_aktau)
        self.client.post(reverse('backoffice:content_eventlandings_create'))
        self.assertEqual(EventLanding.objects.latest('pk').region, self.aktau)

    def test_anonymous_redirected_to_login(self):
        self.client.logout()
        resp = self.client.get(reverse('backoffice:content_eventlandings_list'))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(re.match(re.escape(reverse('backoffice:login')), resp.url))


class EventLandingInlineTests(BackofficeTestCase):
    """EF-11: дни, программа дня, материалы, плитки (formset'ы в одной транзакции)."""

    def setUp(self):
        super().setUp()
        self.day_landing = EventLanding.objects.get(region=self.astana, slug='cambridge-day')
        self.leader = EventLanding.objects.get(region=self.astana, slug='cambridge-programme-leader')
        self.edit_url = reverse(
            'backoffice:content_eventlandings_edit', kwargs={'pk': self.day_landing.pk})

    def _post(self, landing, data):
        return self.client.post(
            reverse('backoffice:content_eventlandings_edit', kwargs={'pk': landing.pk}), data)

    def test_add_day(self):
        data = _edit_data(self.day_landing, self.superuser)
        data.update({
            'days-TOTAL_FORMS': '2',
            'days-1-date': '2026-11-15', 'days-1-start': '10:00', 'days-1-end': '12:00',
        })
        resp = self._post(self.day_landing, data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.day_landing.days.count(), 2)
        self.assertEqual(str(self.day_landing.days.last().date), '2026-11-15')

    def test_day_end_before_start_saves_nothing(self):
        data = _edit_data(self.day_landing, self.superuser)
        data.update({'title_ru': 'Изменённый заголовок', 'days-0-end': '10:00'})
        resp = self._post(self.day_landing, data)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any('Дни · строка 1' in e for e in resp.context['formset_errors']))
        self.assertContains(resp, 'Окончание должно быть позже начала')
        self.day_landing.refresh_from_db()
        self.assertEqual(self.day_landing.title_ru, 'Cambridge Day')
        self.assertEqual(str(self.day_landing.days.get().end), '14:00:00')

    def test_materials_add_and_delete(self):
        count = self.leader.materials.count()
        first = self.leader.materials.first()
        data = _edit_data(self.leader, self.superuser)
        data.update({
            'materials-TOTAL_FORMS': str(count + 1),
            f'materials-{count}-title_ru': 'Новый материал',
            f'materials-{count}-order': '99',
            'materials-0-DELETE': 'on',
        })
        resp = self._post(self.leader, data)
        self.assertEqual(resp.status_code, 302)
        titles = list(self.leader.materials.values_list('title_ru', flat=True))
        self.assertEqual(len(titles), count)
        self.assertIn('Новый материал', titles)
        self.assertFalse(EventLandingMaterial.objects.filter(pk=first.pk).exists())

    def test_tiles_add_and_delete(self):
        count = self.leader.tiles.count()
        first = self.leader.tiles.first()
        data = _edit_data(self.leader, self.superuser)
        data.update({
            'tiles-TOTAL_FORMS': str(count + 1),
            f'tiles-{count}-title_ru': 'Формат',
            f'tiles-{count}-text_ru': 'Очно',
            f'tiles-{count}-order': '99',
            'tiles-0-DELETE': 'on',
        })
        self.assertEqual(self._post(self.leader, data).status_code, 302)
        self.assertEqual(self.leader.tiles.count(), count)
        self.assertTrue(self.leader.tiles.filter(title_ru='Формат', text_ru='Очно').exists())
        self.assertFalse(EventLandingTile.objects.filter(pk=first.pk).exists())

    def test_inline_row_without_ru_title_rejected(self):
        data = _edit_data(self.leader, self.superuser)
        count = self.leader.tiles.count()
        data.update({'tiles-TOTAL_FORMS': str(count + 1), f'tiles-{count}-text_ru': 'Без заголовка'})
        self.assertEqual(self._post(self.leader, data).status_code, 200)
        self.assertEqual(self.leader.tiles.count(), count)


class EventLandingDayPageTests(BackofficeTestCase):
    """EF-11: страница дня — строки программы (порядок, удаление)."""

    def setUp(self):
        super().setUp()
        self.landing = EventLanding.objects.get(region=self.astana, slug='cambridge-day')
        self.day = self.landing.days.get()
        self.url = reverse(
            'backoffice:content_eventlandings_day_edit',
            kwargs={'pk': self.landing.pk, 'dpk': self.day.pk})

    def _data(self):
        return _formset_to_data(EventLandingProgramRowFormSet(instance=self.day, prefix='rows'))

    def test_get_lists_rows(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['row_fs'].forms), 8)

    def test_reorder(self):
        rows = list(self.day.rows.all())
        data = self._data()
        for i in range(len(rows)):  # обратный порядок
            data[f'rows-{i}-order'] = str(len(rows) - i)
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        self.assertEqual(list(self.day.rows.all()), rows[::-1])

    def test_delete_row(self):
        first = self.day.rows.first()
        data = self._data()
        data['rows-0-DELETE'] = 'on'
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        self.assertEqual(self.day.rows.count(), 7)
        self.assertFalse(self.day.rows.filter(pk=first.pk).exists())

    def test_day_of_other_landing_is_404(self):
        other = EventLanding.objects.get(region=self.astana, slug='skills-xxi')
        url = reverse('backoffice:content_eventlandings_day_edit',
                      kwargs={'pk': other.pk, 'dpk': self.day.pk})
        self.assertEqual(self.client.get(url).status_code, 404)


class EventLandingGalleryTests(BackofficeTestCase):
    """EF-11: AJAX-галерея карусели «Школа» (strict-zip при upload, шаг order 10)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media = tempfile.mkdtemp()
        cls._media_override = override_settings(MEDIA_ROOT=cls._media)
        cls._media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._media_override.disable()
        shutil.rmtree(cls._media, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.landing = EventLanding.objects.get(region=self.astana, slug='cambridge-day')

    def _url(self, name, **kw):
        return reverse(f'backoffice:content_eventlandings_gallery_{name}',
                       kwargs={'pk': self.landing.pk, **kw})

    def _upload(self, *files):
        return self.client.post(self._url('upload'), {'images': list(files)})

    def test_upload_detects_orientation_and_zips(self):
        resp = self._upload(_png(400, 200))
        self.assertEqual(resp.status_code, 200)
        img = self.landing.gallery.get()
        self.assertEqual(img.orientation, 'wide')
        self.assertEqual(resp.json()['items'][0]['orientation'], 'wide')
        # wide, wide, tall → strict-zip: wide, tall, wide с шагом 10.
        self._upload(_png(400, 200), _png(200, 400))
        self.assertEqual(
            list(self.landing.gallery.values_list('orientation', 'order')),
            [('wide', 0), ('tall', 10), ('wide', 20)])

    def test_reorder_update_delete(self):
        self._upload(_png(400, 200), _png(200, 400))
        a, b = self.landing.gallery.all()
        resp = self.client.post(
            self._url('reorder'), json.dumps({'order': [b.pk, a.pk]}), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(self.landing.gallery.values_list('pk', 'order')), [(b.pk, 0), (a.pk, 10)])

        resp = self.client.post(
            self._url('update', gpk=a.pk), json.dumps({'alt_text_kk': 'Мектеп'}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        a.refresh_from_db()
        self.assertEqual(a.alt_text_kk, 'Мектеп')

        self.assertEqual(self.client.post(self._url('delete', gpk=a.pk)).status_code, 200)
        self.assertFalse(EventLandingGalleryImage.objects.filter(pk=a.pk).exists())

    def test_upload_without_files_is_400(self):
        self.assertEqual(self.client.post(self._url('upload')).status_code, 400)


class EventLandingRegionScopeInlineTests(BackofficeTestCase):
    """EF-11: менеджер Актау не достаёт галерею и программу дня лендинга Астаны."""

    def test_manager_of_other_region_gets_404(self):
        landing = EventLanding.objects.get(region=self.astana, slug='cambridge-day')
        day = landing.days.get()
        img = EventLandingGalleryImage(landing=landing, image='eventlandings/gallery/x.jpg')
        img.save()
        self.client.force_login(self.manager_aktau)
        pk = {'pk': landing.pk}
        self.assertEqual(self.client.get(reverse(
            'backoffice:content_eventlandings_day_edit', kwargs={**pk, 'dpk': day.pk})).status_code, 404)
        for name, kw in (('upload', {}), ('reorder', {}), ('update', {'gpk': img.pk}),
                         ('delete', {'gpk': img.pk})):
            url = reverse(f'backoffice:content_eventlandings_gallery_{name}', kwargs={**pk, **kw})
            self.assertEqual(self.client.post(url).status_code, 404, name)
        self.assertTrue(EventLandingGalleryImage.objects.filter(pk=img.pk).exists())
