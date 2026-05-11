from django.db import models


class Region(models.Model):
    """
    Тонкий справочник филиалов. Только slug (URL-сегмент) + name (переводимое)
    + два булевых флага: is_default (один регион по умолчанию для root-редиректа)
    и is_active (показывать ли публично, резолвится ли URL `/<lang>/<slug>/`).

    Контактные данные, описания и т.п. — НЕ здесь. Они привязываются к
    региону через FK из соответствующих контент-моделей (Page/Programs/etc).
    """

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
    is_active = models.BooleanField(
        'Активен',
        default=True,
        help_text='Если выключен — регион не показывается в переключателе и URL `/<lang>/<slug>/` возвращает 404. Используется для городов, которые добавлены «на будущее».',
    )

    class Meta:
        verbose_name = 'Регион'
        verbose_name_plural = 'Регионы'
        # Активные первыми, default — наверху активных, далее по slug.
        ordering = ['-is_active', '-is_default', 'slug']
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
        """Активный регион с is_default=True, либо None."""
        return cls.objects.filter(is_default=True, is_active=True).first()
