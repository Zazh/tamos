from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    manager_region = models.ForeignKey(
        'regions.Region',
        verbose_name='Регион менеджера',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managers',
        help_text='Если задан — пользователь видит в админке только данные своего региона. '
                  'У суперадминов оставлять пустым (видят всё).',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
