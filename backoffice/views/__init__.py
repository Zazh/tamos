"""Backoffice views — пакет, разбитый по разделам.

`urls.py` импортирует `from . import views` и обращается как
`views.content_home_edit`, поэтому пакет re-export'ит все view-функции из
подмодулей.

Структура:
  `_common.py`     — `run_translate`, `run_seo`, `auto_slug`, `make_step` и др.
                     общие хелперы, использующиеся в нескольких разделах.
  `auth.py`        — `login`, `logout`.
  `leads.py`       — `leads_list`, `lead_detail`, `lead_quick_status`.
  `content/*.py`   — отдельный модуль на каждый раздел контента.

`dashboard` живёт здесь (а не в `dashboard.py`), потому что одноимённый
модуль конфликтует с attribute lookup при `import backoffice.views.dashboard`.
"""

from django.views.decorators.cache import never_cache

from ..shortcuts import backoffice_required, render_backoffice

from .auth import login, logout  # noqa: F401
from .leads import leads_list, lead_detail, lead_quick_status  # noqa: F401

from .content.home import (  # noqa: F401
    content_home_list,
    content_home_edit,
    content_home_gallery_upload,
    content_home_gallery_reorder,
    content_home_gallery_update,
    content_home_gallery_delete,
    content_home_translate,
    content_home_seo,
)
from .content.contacts import (  # noqa: F401
    content_contacts_list,
    content_contacts_edit,
    content_contacts_translate,
    content_contacts_seo,
)
from .content.program import (  # noqa: F401
    content_program_list,
    content_program_edit,
    content_program_translate,
    content_program_seo,
)
from .content.admission import (  # noqa: F401
    content_admission_list,
    content_admission_edit,
    content_admission_translate,
    content_admission_variant_edit,
    content_admission_variant_translate,
    content_admission_variant_seo,
)
from .content.activities import (  # noqa: F401
    content_activities_list,
    content_activities_region,
    content_activities_save,
    content_activities_activity_add,
    content_activities_activity_delete,
    content_activities_reorder,
    content_activities_translate,
    content_activities_group_add,
    content_activities_group_edit,
    content_activities_group_translate,
    content_activities_group_delete,
)
from .content.blog import (  # noqa: F401
    content_blog_list,
    content_blog_create,
    content_blog_edit,
    content_blog_delete,
    content_blog_gallery_upload,
    content_blog_gallery_reorder,
    content_blog_gallery_update,
    content_blog_gallery_delete,
    content_blog_translate,
    content_blog_seo,
    content_blog_suggest_tags,
    content_blog_taxonomy,
    content_blog_category_save,
    content_blog_category_delete,
    content_blog_tag_save,
    content_blog_tag_delete,
)
from .content.events import (  # noqa: F401
    content_events_list,
    content_events_create,
    content_events_edit,
    content_events_delete,
    content_events_gallery_upload,
    content_events_gallery_reorder,
    content_events_gallery_update,
    content_events_gallery_delete,
    content_events_translate,
    content_events_seo,
)
from .content.flatpages import (  # noqa: F401
    content_flatpages_list,
    content_flatpages_create,
    content_flatpages_edit,
    content_flatpages_delete,
    content_flatpages_translate,
    content_flatpages_seo,
)
from .content.gallery import (  # noqa: F401
    content_gallery_list,
    content_gallery_create,
    content_gallery_edit,
    content_gallery_delete,
    content_gallery_photo_upload,
    content_gallery_photo_toggle,
    content_gallery_photo_update,
    content_gallery_photo_delete,
    content_gallery_photo_translate,
    content_gallery_taxonomy,
    content_gallery_category_save,
    content_gallery_category_delete,
)
from .content.team import (  # noqa: F401
    content_team_list,
    content_team_region,
    content_team_reorder,
    content_team_create,
    content_team_edit,
    content_team_delete,
    content_team_translate,
    content_team_seo,
)
from .site import (  # noqa: F401
    site_menu_list,
    site_menu_create,
    site_menu_edit,
    site_menu_delete,
    site_menu_item_delete,
)
from .settings import (  # noqa: F401
    settings_regions_list,
    settings_regions_create,
    settings_regions_edit,
    settings_regions_delete,
    settings_users_list,
    settings_users_create,
    settings_users_edit,
    settings_users_password,
    settings_users_delete,
)


@never_cache
@backoffice_required
def dashboard(request):
    return render_backoffice(
        request,
        'backoffice/dashboard.html',
        active='dashboard',
        page_title='Дашборд',
    )
