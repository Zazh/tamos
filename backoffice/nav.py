"""Sidebar navigation for backoffice.

Каждая item.url либо ссылается на свой backoffice-view, либо на admin
(fallback, пока native UI не построен — менеджер сразу попадает на edit-форму).

При появлении native view: поменять `url_name` у item — `external` уходит.

`build_nav(user)` дополнительно считает «алерт-счётчики» — число элементов
требующих внимания (например, новые заявки) — и кладёт их в `item.badge`.
Шаблон рисует красный pill + `.has-alert` подсветку на пункте.
"""

from django.urls import NoReverseMatch, reverse


def _admin(app_label: str, model: str) -> str:
    """Reverse admin changelist URL, или '#' если нет регистрации."""
    try:
        return reverse(f'admin:{app_label}_{model}_changelist')
    except NoReverseMatch:
        return '#'


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
    """
    new_leads = _count_new_leads(user)

    return [
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
                {'id': 'admission', 'label': 'Поступление', 'icon': 'target', 'url': _own('content_admission_list')},
                {'id': 'activities', 'label': 'Активности', 'icon': 'pulse', 'url': _admin('activities', 'activity'), 'external': True},
            ],
        },
        {
            'id': 'feed',
            'label': 'Лента',
            'items': [
                {'id': 'blog', 'label': 'Блог', 'icon': 'newspaper', 'url': _admin('blog', 'blogpost'), 'external': True},
                {'id': 'events', 'label': 'События', 'icon': 'sparkles', 'url': _admin('events', 'event'), 'external': True},
                {'id': 'gallery', 'label': 'Галерея', 'icon': 'image', 'url': _admin('gallery', 'galleryimage'), 'external': True},
                {'id': 'flatpages', 'label': 'Доп. страницы', 'icon': 'file', 'url': _admin('pages', 'flatpage'), 'external': True},
            ],
        },
        {
            'id': 'site',
            'label': 'Сайт',
            'items': [
                {'id': 'navigation', 'label': 'Меню', 'icon': 'menu', 'url': _admin('navigation', 'navsection'), 'external': True},
            ],
        },
        {
            'id': 'settings',
            'label': 'Настройки',
            'items': [
                {'id': 'regions', 'label': 'Регионы', 'icon': 'pin', 'url': _admin('regions', 'region'), 'external': True},
                {'id': 'users', 'label': 'Пользователи', 'icon': 'users', 'url': _admin('accounts', 'user'), 'external': True},
            ],
        },
    ]
