from modeltranslation.translator import TranslationOptions, register

from .models import Activity, ActivityGroup, ActivitySection


@register(ActivitySection)
class ActivitySectionTranslationOptions(TranslationOptions):
    fields = ('title',)


@register(Activity)
class ActivityTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'location')


@register(ActivityGroup)
class ActivityGroupTranslationOptions(TranslationOptions):
    fields = ('label', 'teacher_name', 'teacher_bio')
