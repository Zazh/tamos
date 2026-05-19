"""Backoffice forms — пакет, разбитый по разделам.

`views.*` импортирует имена с уровня пакета (`from ..forms import HomePageEditForm`),
поэтому `__init__.py` re-export'ит всё из подмодулей.

Файлы:
  `_common.py`     — `_localized`, `_strip_lang`, `_apply_backoffice_widget_classes`,
                     `apply_out_of_form_attrs`, `setup_region_field`, `FileSizeMixin`,
                     `_relax_required`, `_limit_chars`, `hide_slug_field`.
  `auth.py`        — `LoginForm`.
  `leads.py`       — `LeadEditForm`.
  `content/*.py`   — формы и formset'ы по разделам контента.
"""

from ._common import TRANSLATION_LANGS  # noqa: F401

from .auth import LoginForm  # noqa: F401
from .leads import LeadEditForm  # noqa: F401

from .content.home import HOME_TRANSLATABLE, HomePageEditForm  # noqa: F401
from .content.contacts import (  # noqa: F401
    CONTACTS_TRANSLATABLE,
    ContactsDepartmentFormSet,
    ContactsDepartmentItemForm,
    ContactsPageEditForm,
)
from .content.program import (  # noqa: F401
    PROGRAM_FIXED_SLOT_COUNT,
    PROGRAM_FIXED_SLOT_SECTIONS,
    PROGRAM_INLINE_FORMSETS,
    PROGRAM_TRANSLATABLE,
    ProgramAudienceFormSet,
    ProgramAudienceItemForm,
    ProgramBenefitFormSet,
    ProgramBenefitItemForm,
    ProgramCertificateFeatureForm,
    ProgramCertificateFeatureFormSet,
    ProgramFaqFormSet,
    ProgramFaqItemForm,
    ProgramPageEditForm,
    ProgramStatForm,
    ProgramStatFormSet,
    ProgramVariantCardForm,
    ProgramVariantFormSet,
)
from .content.admission import (  # noqa: F401
    ADMISSION_PAGE_INLINE_FORMSETS,
    ADMISSION_PAGE_TRANSLATABLE,
    ADMISSION_VARIANT_FIXED_SLOT_COUNT,
    ADMISSION_VARIANT_FIXED_SLOT_SECTIONS,
    ADMISSION_VARIANT_INLINE_FORMSETS,
    ADMISSION_VARIANT_TRANSLATABLE,
    AdmissionDocumentForm,
    AdmissionDocumentFormSet,
    AdmissionIncludedItemForm,
    AdmissionIncludedItemFormSet,
    AdmissionPageEditForm,
    AdmissionPricingPlanForm,
    AdmissionPricingPlanFormSet,
    AdmissionTestingFeatureForm,
    AdmissionTestingFeatureFormSet,
    AdmissionVariantEditForm,
)
from .content.activities import (  # noqa: F401
    ACTIVITY_GROUP_TRANSLATABLE,
    ACTIVITY_TRANSLATABLE,
    ActivityEditForm,
    ActivityGroupForm,
    ActivityGroupFormSet,
    ScheduleSlotForm,
    ScheduleSlotFormSet,
)
from .content.blog import (  # noqa: F401
    BLOG_POST_OUT_OF_FORM_BASES,
    BLOG_POST_TRANSLATABLE,
    BlogCategoryCreateForm,
    BlogCategoryItemForm,
    BlogPostEditForm,
    BlogTagCreateForm,
    BlogTagItemForm,
)
from .content.events import (  # noqa: F401
    EVENT_OUT_OF_FORM_BASES,
    EVENT_TRANSLATABLE,
    EventEditForm,
)
from .content.flatpages import (  # noqa: F401
    FLATPAGE_OUT_OF_FORM_BASES,
    FLATPAGE_TRANSLATABLE,
    FlatPageEditForm,
)
from .content.gallery import (  # noqa: F401
    ALBUM_TRANSLATABLE,
    AlbumEditForm,
    GALLERY_IMAGE_TRANSLATABLE,
    GalleryCategoryCreateForm,
    GalleryCategoryItemForm,
    GalleryImageEditForm,
)
from .content.team import (  # noqa: F401
    TEAM_MEMBER_OUT_OF_FORM_BASES,
    TEAM_MEMBER_TRANSLATABLE,
    TeamMemberEditForm,
)
from .site import (  # noqa: F401
    NAV_ITEM_TRANSLATABLE,
    NAV_SECTION_TRANSLATABLE,
    NavItemEditForm,
    NavItemFormSet,
    NavSectionCreateForm,
    NavSectionEditForm,
)
from .settings import (  # noqa: F401
    REGION_TRANSLATABLE,
    ROLE_CHOICES,
    ROLE_DESCRIPTIONS,
    ROLE_MANAGER,
    ROLE_NONE,
    ROLE_SUPERADMIN,
    RegionCreateForm,
    RegionEditForm,
    UserCreateForm,
    UserEditForm,
    UserPasswordForm,
)
