from modeltranslation.translator import TranslationOptions, register

from .models import Activity, ActivityGroup, ActivitySection, Teacher


@register(ActivitySection)
class ActivitySectionTranslationOptions(TranslationOptions):
    fields = ('title',)


@register(Teacher)
class TeacherTranslationOptions(TranslationOptions):
    fields = ('name', 'bio')


@register(Activity)
class ActivityTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'location')


@register(ActivityGroup)
class ActivityGroupTranslationOptions(TranslationOptions):
    fields = ('label',)
