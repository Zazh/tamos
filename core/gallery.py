"""Общая логика ориентированной галереи (карусель «О Space School»).

`orientation` (wide/tall/square) определяется по соотношению сторон при save()
и задаёт CSS-слот в `carousel.css` (.carousel-item-wide / -tall / -square).
Порядок показа — `strict_zip_arrange` во view (W, T, W, T… + хвост + square).

Наследники (`pages.HomeGalleryImage`, `eventlandings.EventLandingGalleryImage`)
сами объявляют `image` (свой `upload_to`) и `alt_text`.
"""
from django.db import models


class Orientation(models.TextChoices):
    WIDE = 'wide', 'Широкая'      # ratio > 1.15  → слот 342×223
    TALL = 'tall', 'Высокая'      # ratio < 0.95  → слот 325×352
    SQUARE = 'square', 'Квадратная'


def detect_orientation(image_field) -> str:
    """Открыть оригинал через Pillow, вычислить ratio width/height.

    - ratio > 1.15 → wide (горизонтальная)
    - ratio < 0.95 → tall (вертикальная)
    - между      → square (квадратная)

    Если файл недоступен / не открывается — square (безопасный дефолт).
    """
    from PIL import Image, UnidentifiedImageError
    try:
        with Image.open(image_field) as im:
            w, h = im.size
    except (FileNotFoundError, UnidentifiedImageError, OSError):
        return Orientation.SQUARE
    if h == 0:
        return Orientation.SQUARE
    ratio = w / h
    if ratio > 1.15:
        return Orientation.WIDE
    if ratio < 0.95:
        return Orientation.TALL
    return Orientation.SQUARE


def strict_zip_arrange(images):
    """Расставить картинки в строгом порядке: wide → tall → wide → tall →…

    - Сначала идут чередующиеся пары (W, T, W, T, …) пока есть запас обоих
    - Хвост (оставшиеся wide или tall) приклеивается в конец
    - Square — всегда в конец

    Не сохраняет в БД — возвращает упорядоченный список. Порядок внутри
    каждой группы сохраняется (по текущему order, потом по pk).
    """
    sorted_imgs = sorted(images, key=lambda i: (i.order, i.pk))
    wide = [i for i in sorted_imgs if i.orientation == Orientation.WIDE]
    tall = [i for i in sorted_imgs if i.orientation == Orientation.TALL]
    square = [i for i in sorted_imgs if i.orientation == Orientation.SQUARE]

    result = []
    while wide and tall:
        result.append(wide.pop(0))
        result.append(tall.pop(0))
    result.extend(wide)
    result.extend(tall)
    result.extend(square)
    return result


class OrientedGalleryImage(models.Model):
    """Абстрактная картинка карусели: авто-`orientation` + `order`."""

    orientation = models.CharField(
        'Ориентация',
        max_length=8,
        choices=Orientation.choices,
        default=Orientation.SQUARE,
        help_text='Определяется автоматически при загрузке (wide/tall/square).',
    )
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        abstract = True
        ordering = ['order', 'pk']

    def save(self, *args, **kwargs):
        if self.image and (
            not self.pk
            or 'image' in (kwargs.get('update_fields') or ())
            or self._image_changed()
        ):
            self.orientation = detect_orientation(self.image)
        super().save(*args, **kwargs)

    def _image_changed(self) -> bool:
        if not self.pk:
            return True
        try:
            old = type(self).objects.only('image').get(pk=self.pk)
        except type(self).DoesNotExist:
            return True
        return old.image.name != self.image.name
