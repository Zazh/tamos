"""Массовый импорт фото в `GalleryImage` с Pillow-пайплайном.

Пайплайн на каждый файл:
  1. PIL.Image.open
  2. ImageOps.exif_transpose — учесть EXIF-ориентацию
  3. convert('RGB') для RGBA/P (JPEG не поддерживает альфу)
  4. thumbnail((MAX, MAX)) — даунскейл по длинной стороне до MAX_DIMENSION
  5. save(JPEG, quality=JPEG_QUALITY, optimize=True, progressive=True)

ImageSpecField (`image_webp`, `image_compressed`) поверх делает свои
варианты (webp + compressed JPEG) лениво при первом обращении из шаблона.

Каждый N-й файл (по умолчанию N=4) помечается is_wide=True —
повторяет визуальный ритм mosaic-сетки из прототипа.

Использование:
    docker compose exec tamosapp python manage.py import_gallery \\
        /app/spaceschool/docs/gallery --category=school-life --region=astana
"""
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from gallery.models import GalleryCategory, GalleryImage
from regions.models import Region


SUPPORTED_EXT = {'.jpg', '.jpeg', '.png', '.webp'}
MAX_DIMENSION = 2400  # px по длинной стороне
JPEG_QUALITY = 90


class Command(BaseCommand):
    help = (
        'Импортирует все фото из указанной директории в GalleryImage. '
        'Прогон через Pillow: exif_transpose + thumbnail + JPEG q=90 + progressive.'
    )

    def add_arguments(self, parser):
        parser.add_argument('source_dir', type=str, help='Директория с исходниками')
        parser.add_argument('--region', default='astana',
                            help='Slug региона (default: astana)')
        parser.add_argument('--category', default=None,
                            help='Slug категории. Если не задан — None.')
        parser.add_argument('--start-order', type=int, default=0,
                            help='Стартовое значение order (default: 0)')
        parser.add_argument('--wide-every', type=int, default=4,
                            help='Каждый N-й помечается is_wide=True (0 — не помечать)')
        parser.add_argument('--alt', default='',
                            help='Общий alt-текст для всех фото (опционально)')

    def handle(self, *args, **opts):
        source_dir = Path(opts['source_dir'])
        if not source_dir.is_dir():
            raise CommandError(f'Не директория: {source_dir}')

        try:
            region = Region.objects.get(slug=opts['region'])
        except Region.DoesNotExist as exc:
            raise CommandError(f"Регион '{opts['region']}' не найден") from exc

        category = None
        if opts['category']:
            try:
                category = GalleryCategory.objects.get(slug=opts['category'])
            except GalleryCategory.DoesNotExist as exc:
                raise CommandError(f"Категория '{opts['category']}' не найдена") from exc

        files = sorted(
            p for p in source_dir.iterdir()
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXT
        )
        if not files:
            self.stdout.write(self.style.WARNING(f'Нет файлов в {source_dir}'))
            return

        wide_every = opts['wide_every']
        alt = opts['alt']
        created = 0

        for idx, path in enumerate(files):
            order = opts['start_order'] + idx
            is_wide = bool(wide_every) and (idx % wide_every == 0)
            try:
                content, out_name = self._process(path)
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'{path.name}: {exc}'))
                continue

            gi = GalleryImage(
                region=region,
                category=category,
                alt=alt,
                alt_ru=alt,
                order=order,
                is_wide=is_wide,
                is_published=True,
            )
            gi.image.save(out_name, content, save=False)
            gi.save()
            created += 1
            self.stdout.write(
                f'  · {path.name} → order={order} wide={is_wide} '
                f'size={len(content):,}B'
            )

        self.stdout.write(self.style.SUCCESS(
            f'Импортировано {created}/{len(files)} в region={region.slug} '
            f'category={opts["category"] or "—"}'
        ))

    def _process(self, path: Path) -> tuple[ContentFile, str]:
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im)
            if im.mode not in ('RGB', 'L'):
                im = im.convert('RGB')
            if max(im.size) > MAX_DIMENSION:
                im.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

            buf = BytesIO()
            im.save(
                buf,
                format='JPEG',
                quality=JPEG_QUALITY,
                optimize=True,
                progressive=True,
            )

        buf.seek(0)
        return ContentFile(buf.read(), name=path.stem + '.jpg'), path.stem + '.jpg'
