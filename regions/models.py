from django.core.exceptions import ValidationError
from django.db import models


class Region(models.Model):
    slug = models.SlugField(
        unique=True,
        max_length=32,
        help_text='Сегмент в URL: astana, aktau. Только латиница.',
    )
    name = models.CharField('Название', max_length=100)
    is_default = models.BooleanField(
        'Регион по умолчанию',
        default=False,
        help_text='Пометить ровно один регион. Для корневого URL и для пользователей без выбора.',
    )
    phone = models.CharField('Телефон', max_length=64, blank=True)
    address = models.CharField('Адрес', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Регион'
        verbose_name_plural = 'Регионы'
        # Default region первым — нужно для всяких inline-перечислений
        # вида «Astana, Aktau» в meta-описаниях.
        ordering = ['-is_default', 'slug']
        constraints = [
            models.UniqueConstraint(
                fields=['is_default'],
                condition=models.Q(is_default=True),
                name='regions_only_one_default',
            ),
        ]

    def __str__(self):
        return self.name or self.slug

    @classmethod
    def get_default(cls):
        return cls.objects.filter(is_default=True).first()
