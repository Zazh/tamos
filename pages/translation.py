from modeltranslation.translator import TranslationOptions, register

from .models import ContactsDepartment, ContactsPage, HomeGalleryImage, HomePage


@register(HomePage)
class HomePageTranslationOptions(TranslationOptions):
    fields = (
        'hero_badge_text',
        'hero_title',
        'hero_subtitle',
        'hero_cta_primary_text',
        'hero_cta_secondary_text',
        'about_label',
        'about_title',
        'about_body',
    )


@register(HomeGalleryImage)
class HomeGalleryImageTranslationOptions(TranslationOptions):
    fields = ('alt_text',)


@register(ContactsPage)
class ContactsPageTranslationOptions(TranslationOptions):
    fields = (
        'intro_title',
        'intro_text',
        'office_name',
        'office_address',
        'office_hours',
    )


@register(ContactsDepartment)
class ContactsDepartmentTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'hours')
