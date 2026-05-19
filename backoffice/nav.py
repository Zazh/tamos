"""Sidebar navigation for backoffice.

Все пункты — native backoffice views.

`build_nav(user)` дополнительно считает «алерт-счётчики» — число элементов
требующих внимания (например, новые заявки) — и кладёт их в `item.badge`.
Шаблон рисует красный pill + `.has-alert` подсветку на пункте.

Секции `site` (Меню) и `settings` (Регионы, Пользователи) видны только
суперадмину — это глобальные инфра-справочники.
"""

from django.urls import NoReverseMatch, reverse


def _own(name: str) -> str:
    """Reverse backoffice URL, или '#' если ещё не определена."""
    try:
        return reverse(f'backoffice:{name}')
    except NoReverseMatch:
        return '#'


def _count_new_leads(user) -> int:
    """Region-scoped счётчик заявок со статусом NEW для подсветки в sidebar.

    Считает 1 query на каждый render backoffice-страницы — приемлемо для
    малотрафичного backoffice. При росте — закешировать на 30-60 сек.
    """
    if user is None or not user.is_authenticated:
        return 0
    # Lazy import — избегаем циклической зависимости на app-loading.
    from feedback.models import Lead
    qs = Lead.objects.filter(status=Lead.Status.NEW)
    if user.is_superuser:
        return qs.count()
    if getattr(user, 'manager_region_id', None):
        return qs.filter(region_id=user.manager_region_id).count()
    return 0


def build_nav(user=None):
    """Возвращает список секций. Резолв URL на каждом запросе — дёшево.

    Структура:
        [
          {id, label?, items: [
              {id, label, icon, url, external?, badge?}
          ]}
        ]

    `external=True` означает «уходим в Django admin» — отрисуем стрелочку.
    `badge` — необязательное число (новые заявки и т.п.), считается per-user
    с учётом region-scope.

    Секции `site` и `settings` показываются только суперадмину — это
    инфра-справочники (навигация, регионы, юзеры), менеджеры туда не лезут.
    """
    new_leads = _count_new_leads(user)
    is_superuser = bool(user and getattr(user, 'is_superuser', False))

    sections = [
        {
            'id': 'main',
            'items': [
                {'id': 'dashboard', 'label': 'Дашборд', 'icon': 'dashboard', 'url': _own('dashboard')},
                {'id': 'leads', 'label': 'Заявки', 'icon': 'inbox', 'url': _own('leads_list'),
                 'badge': new_leads if new_leads else None},
            ],
        },
        {
            'id': 'content',
            'label': 'Контент',
            'items': [
                {'id': 'home', 'label': 'Главная', 'icon': 'home', 'url': _own('content_home_list')},
                {'id': 'contacts', 'label': 'Контакты', 'icon': 'phone', 'url': _own('content_contacts_list')},
                {'id': 'programs', 'label': 'Программа', 'icon': 'cap', 'url': _own('content_program_list')},
                {'id': 'team', 'label': 'Команда', 'icon': 'users', 'url': _own('content_team_list')},
                {'id': 'admission', 'label': 'Поступление', 'icon': 'target', 'url': _own('content_admission_list')},
                {'id': 'activities', 'label': 'Активности', 'icon': 'pulse', 'url': _own('content_activities_list')},
                {'id': 'footer', 'label': 'Футер', 'icon': 'file', 'url': _own('content_footer_list')},
            ],
        },
        {
            'id': 'feed',
            'label': 'Лента',
            'items': [
                {'id': 'blog', 'label': 'Блог', 'icon': 'newspaper', 'url': _own('content_blog_list')},
                {'id': 'events', 'label': 'События', 'icon': 'sparkles', 'url': _own('content_events_list')},
                {'id': 'gallery', 'label': 'Галерея', 'icon': 'image', 'url': _own('content_gallery_list')},
                {'id': 'flatpages', 'label': 'Доп. страницы', 'icon': 'file', 'url': _own('content_flatpages_list')},
            ],
        },
    ]

    if is_superuser:
        sections.append({
            'id': 'site',
            'label': 'Сайт',
            'items': [
                {'id': 'navigation', 'label': 'Меню', 'icon': 'menu', 'url': _own('site_menu_list')},
            ],
        })
        sections.append({
            'id': 'settings',
            'label': 'Настройки',
            'items': [
                {'id': 'regions', 'label': 'Регионы', 'icon': 'pin', 'url': _own('settings_regions_list')},
                {'id': 'users', 'label': 'Пользователи', 'icon': 'shield', 'url': _own('settings_users_list')},
            ],
        })

    return sections
