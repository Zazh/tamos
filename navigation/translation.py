from modeltranslation.translator import TranslationOptions, register

from .models import NavItem, NavSection


@register(NavSection)
class NavSectionTranslationOptions(TranslationOptions):
    fields = ('label',)


@register(NavItem)
class NavItemTranslationOptions(TranslationOptions):
    fields = ('label',)
