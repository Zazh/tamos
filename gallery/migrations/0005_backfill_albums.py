"""Backfill: для существующих GalleryImage'ов создаём «дефолтные» альбомы
по парам (region × category) и привязываем фото к ним.

Идемпотентна: повторный прогон ничего не создаёт (update_or_create по
(region, slug)). Reverse — снимает album=NULL у тех фото, у которых был
создан дефолтный альбом, и удаляет эти альбомы.
"""

from django.db import migrations
from django.utils import timezone


DEFAULT_SLUG_PREFIX = 'default-'


def make_default_slug(category_slug: str) -> str:
    """Slug дефолтного альбома: `default-<category-slug>` (или `default-uncategorized`)."""
    return f'{DEFAULT_SLUG_PREFIX}{category_slug or "uncategorized"}'


def backfill_albums(apps, schema_editor):
    Album = apps.get_model('gallery', 'Album')
    GalleryCategory = apps.get_model('gallery', 'GalleryCategory')
    GalleryImage = apps.get_model('gallery', 'GalleryImage')
    Region = apps.get_model('regions', 'Region')

    # Уже привязанные фото — пропускаем (idempotent re-run).
    qs = GalleryImage.objects.filter(album__isnull=True)
    pairs = qs.values_list('region_id', 'category_id').distinct()

    # «Без категории» (category_id=None) → требуется fallback. Берём
    # первую опубликованную категорию региона или первую вообще; если в БД
    # нет ни одной — не привязываем (фото останутся album=NULL, на сайт не
    # попадут — это пограничный случай, поправляется в backoffice вручную).
    fallback_category = GalleryCategory.objects.filter(is_published=True).order_by('order', 'name').first()
    if fallback_category is None:
        fallback_category = GalleryCategory.objects.order_by('order', 'name').first()

    now = timezone.now()

    for region_id, category_id in pairs:
        if category_id is None:
            if fallback_category is None:
                continue
            category_id = fallback_category.pk

        category = GalleryCategory.objects.get(pk=category_id)
        region = Region.objects.get(pk=region_id)

        slug = make_default_slug(category.slug)
        album_title = f'Архив · {category.name}'

        album, _created = Album.objects.update_or_create(
            region=region,
            slug=slug,
            defaults={
                'category': category,
                'title': album_title,
                'title_ru': album_title,
                'lead': 'Альбом создан автоматически при переходе на новую модель галереи.',
                'lead_ru': 'Альбом создан автоматически при переходе на новую модель галереи.',
                'is_published': True,
                'updated_at': now,
            },
        )

        # Привязываем все фото этого (region, category) к нему. Для NULL-категории —
        # фото переходят в fallback-альбом.
        original_filter = {'region_id': region_id, 'album__isnull': True}
        if category_id == fallback_category.pk:
            original_filter['category_id__in'] = [None, fallback_category.pk]
            # Отдельно: NULL и явный fallback (Django не умеет __in=[None, x]).
            GalleryImage.objects.filter(
                region_id=region_id,
                album__isnull=True,
                category__isnull=True,
            ).update(album=album)
        GalleryImage.objects.filter(
            region_id=region_id,
            album__isnull=True,
            category_id=category_id,
        ).update(album=album)


def remove_default_albums(apps, schema_editor):
    Album = apps.get_model('gallery', 'Album')
    GalleryImage = apps.get_model('gallery', 'GalleryImage')

    auto_albums = Album.objects.filter(slug__startswith=DEFAULT_SLUG_PREFIX)
    if not auto_albums.exists():
        return

    # Отвязываем фото
    GalleryImage.objects.filter(album__in=auto_albums).update(album=None)
    auto_albums.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0004_alter_galleryimage_options_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_albums, remove_default_albums),
    ]
