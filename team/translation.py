from modeltranslation.translator import TranslationOptions, register

from .models import TeamMember


@register(TeamMember)
class TeamMemberTranslationOptions(TranslationOptions):
    fields = (
        'name',
        'role',
        'meta',
        'quote',
        'bio',
        'seo_title',
        'seo_description',
        'og_title',
        'og_description',
    )
