from modeltranslation.translator import TranslationOptions, register

from .models import ContactsDepartment, ContactsPage, FlatPage, HomeGalleryImage, HomePage


@register(HomePage)
class HomePageTranslationOptions(TranslationOptions):
    fields = (
        'hero_badge_text',
        'hero_title',
        'hero_subtitle',
        'hero_cta_primary_text',
        'hero_cta_primary_modal_title',
        'hero_cta_secondary_text',
        'hero_cta_secondary_modal_title',
        'about_label',
        'about_title',
        'about_body',
        'seo_title',
        'seo_description',
        'og_title',
        'og_description',
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
        'seo_title',
        'seo_description',
        'og_title',
        'og_description',
    )


@register(ContactsDepartment)
class ContactsDepartmentTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'hours')


@register(FlatPage)
class FlatPageTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'lead',
        'content',
        'cover_caption',
        'cover_alt',
        'seo_title',
        'seo_description',
        'og_title',
        'og_description',
    )
