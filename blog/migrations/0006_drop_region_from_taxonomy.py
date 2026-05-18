"""Смерж дубликатов BlogCategory/BlogTag по slug.

Категории/теги становятся глобальными (см. 0007 для schema-части миграции).
Эта миграция только data: смержить дубликаты по slug, перенаправить ссылки
из BlogPost.category и BlogPost.tags на канонические (минимальный pk),
удалить лишние.

Разделено на две миграции: PostgreSQL не выполняет data + schema (RemoveField FK)
в одной транзакции из-за «pending trigger events».
"""

from django.db import migrations


def _merge_dupes_by_slug(model, post_field_name, apps):
    BlogPost = apps.get_model('blog', 'BlogPost')

    seen_by_slug = {}
    duplicates = []
    for obj in model.objects.order_by('pk'):
        canonical = seen_by_slug.get(obj.slug)
        if canonical is None:
            seen_by_slug[obj.slug] = obj
        else:
            duplicates.append((obj, canonical))

    for dup, canonical in duplicates:
        if post_field_name == 'category':
            BlogPost.objects.filter(category=dup).update(category=canonical)
        elif post_field_name == 'tags':
            for post in BlogPost.objects.filter(tags=dup):
                post.tags.remove(dup)
                post.tags.add(canonical)
        dup.delete()


def merge_taxonomy_duplicates(apps, schema_editor):
    BlogCategory = apps.get_model('blog', 'BlogCategory')
    BlogTag = apps.get_model('blog', 'BlogTag')
    _merge_dupes_by_slug(BlogCategory, 'category', apps)
    _merge_dupes_by_slug(BlogTag, 'tags', apps)


def noop(apps, schema_editor):
    """Reverse — смерж не разворачивается; для отката сначала откатите 0007,
    затем при необходимости пересейте через 0002."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0005_blogpost_seo_fields'),
    ]

    operations = [
        migrations.RunPython(merge_taxonomy_duplicates, reverse_code=noop),
    ]
