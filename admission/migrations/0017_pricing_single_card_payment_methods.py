"""Прайс «Поступление»: одна карта + список способов оплаты; казахское 7–11 убрано.

ТЗ школы (октябрь 2026): три колонки «100% до 1 июня / Ежеквартально / Годовая
оплата» устарели — 1 июня прошло, учебный год идёт. Вместо них на каждом варианте:

  * одна прайс-карта «Стоимость обучения — 4 284 000 ₸ / За 2026–2027 учебный год»
    (цена колонки «Годовая оплата» — единственная, не привязанная к 1 июня);
  * под ценой и текстом про взнос — фраза + нумерованный список из 3 способов
    оплаты (`AdmissionPage.payment_methods_title` + inline `AdmissionPaymentMethod`,
    общие для всех вариантов региона);
  * в `pricing_lead` «После выбора тарифа» → «После выбора способа оплаты».

Казахского отделения 7–11 классов нет → удаляем варианты (kz × 7-11) во всех
регионах и саму GradeGroup `7-11` (другими отделениями не используется).

Все данные inline — миграция не импортирует `seed_data` (см. memory
feedback_seed_migrations_brittle). Идемпотентна: прайс пересобирается только у
вариантов, где ещё лежат карты с «1 июня»; способы оплаты создаются только если
у страницы их нет; ручные правки менеджеров не затираются.
Reverse — no-op (старые карты не восстанавливаем, kz×7-11 не пересоздаём).
"""
from django.db import migrations


LANGS = ('ru', 'kk', 'en')

PAYMENT_METHODS_TITLE = {
    'ru': 'Оплату можно совершать тремя удобными для вас способами:',
    'kk': 'Төлемді сізге ыңғайлы үш тәсілмен жасауға болады:',
    'en': 'Payment can be made in three convenient ways:',
}

PAYMENT_METHODS = [
    {
        'ru': '100% оплата за год',
        'kk': 'Жыл үшін 100% төлем',
        'en': '100% payment for the year',
    },
    {
        'ru': 'В 3 транша (20 августа, 20 ноября, 20 февраля)',
        'kk': '3 траншпен (20 тамыз, 20 қараша, 20 ақпан)',
        'en': 'In 3 instalments (20 August, 20 November, 20 February)',
    },
    {
        'ru': 'Ежемесячно (сумма делится на 9 месяцев)',
        'kk': 'Ай сайын (сома 9 айға бөлінеді)',
        'en': 'Monthly (the amount is split over 9 months)',
    },
]

PLAN_LABEL = {
    'ru': 'Стоимость обучения',
    'kk': 'Оқу құны',
    'en': 'Tuition fee',
}
PLAN_NOTE = {
    'ru': 'За 2026–2027 учебный год',
    'kk': '2026–2027 оқу жылына',
    'en': 'For the 2026–2027 academic year',
}
PLAN_PRICE_VALUE = '4 284 000'
PLAN_CURRENCY = '₸'

# Маркеры устаревшего прайса (label/note на любом языке).
LEGACY_MARKERS = ('1 июня', '1 маусым', 'June 1', '1 June')

# `pricing_lead`: «после выбора тарифа» → «после выбора способа оплаты».
# Подстрочная замена — только там, где фраза реально есть.
LEAD_REPLACEMENTS = {
    'ru': [('После выбора тарифа', 'После выбора способа оплаты')],
    'kk': [('Тарифті таңдағаннан кейін', 'Төлем тәсілін таңдағаннан кейін')],
    'en': [('a plan', 'a payment option')],
}

# Иконка прайс-карты (копия ICON_PRICE_STAR из seed_data на момент миграции).
ICON_PRICE_STAR = ''.join(
    '<svg class="aspect-square w-8" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/'
    '2000/svg"><path d="M22.4995 9.62246C22.4318 9.42032 22.3066 9.24233 22.139 9.11023C21.97'
    '14 8.97813 21.7686 8.89762 21.5557 8.87871L15.3853 8.32418L12.9472 2.59137C12.8642 2.395'
    '36 12.7253 2.22813 12.5478 2.11055C12.3702 1.99296 12.1619 1.93019 11.9489 1.93005C11.73'
    '59 1.92991 11.5275 1.99241 11.3498 2.10977C11.1721 2.22712 11.0331 2.39417 10.9498 2.590'
    '08L8.51171 8.32418L2.34374 8.87871C2.13139 8.89753 1.92895 8.97744 1.76172 9.10872C1.594'
    '48 9.24001 1.46961 9.41703 1.40233 9.61829C1.33505 9.81956 1.32827 10.0362 1.38283 10.24'
    '13C1.43738 10.4463 1.55093 10.6309 1.70952 10.7724L6.42937 14.9377L5.00226 21.0552C4.952'
    '52 21.2629 4.96574 21.4807 5.04025 21.6809C5.11476 21.881 5.24722 22.0544 5.42068 22.179'
    'C5.59414 22.3036 5.80082 22.3736 6.01421 22.3801C6.2276 22.3866 6.43815 22.3294 6.61882 '
    '22.2156L11.9994 18.8821L17.3791 22.2156C17.5631 22.3296 17.7775 22.3848 17.9938 22.3737C'
    '18.21 22.3626 18.4177 22.2857 18.5891 22.1534C18.7605 22.0211 18.8874 21.8395 18.9531 21'
    '.633C19.0188 21.4264 19.0202 21.2046 18.9572 20.9973L17.0698 14.9405L21.7785 10.7762C21.'
    '9404 10.6358 22.0577 10.4506 22.1156 10.244C22.1735 10.0374 22.1693 9.81845 22.1036 9.61'
    '402L22.4995 9.62246ZM15.1817 13.8005C15.0349 13.93 14.9279 14.0982 14.8732 14.2859C14.81'
    '86 14.4736 14.8186 14.6731 14.8732 14.8608L16.2872 19.4002L12.5836 17.1006C12.4096 16.99'
    '29 12.2089 16.9358 12.0042 16.9358C11.7995 16.9358 11.5988 16.9929 11.4247 17.1006L7.711'
    '71 19.4002L8.79453 14.8608C8.84913 14.6731 8.84913 14.4736 8.79453 14.2859C8.73992 14.09'
    '82 8.63288 13.93 8.48609 13.8005L4.93874 10.6727L9.55546 10.2596C9.74894 10.2438 9.93396'
    ' 10.1733 10.0884 10.0566C10.2428 9.93982 10.36 9.78167 10.4258 9.59989L11.9994 5.27199L1'
    '3.5919 9.59989C13.6577 9.78167 13.7748 9.93982 13.9293 10.0566C14.0837 10.1733 14.2687 1'
    '0.2438 14.4622 10.2596L19.0789 10.6727L15.1817 13.8005Z" fill="#008ED6"/></svg>'
)


def _is_legacy_plan(plan):
    for lang in LANGS:
        for field in ('label', 'note'):
            value = getattr(plan, f'{field}_{lang}', None) or ''
            if any(marker in value for marker in LEGACY_MARKERS):
                return True
    return False


def _remove_kz_7_11(apps):
    AdmissionVariant = apps.get_model('admission', 'AdmissionVariant')
    GradeGroup = apps.get_model('admission', 'GradeGroup')

    AdmissionVariant.objects.filter(department__slug='kz', grade__slug='7-11').delete()
    # Справочную группу удаляем только если её больше никто не использует.
    GradeGroup.objects.filter(slug='7-11', variants__isnull=True).delete()


def _seed_payment_methods(apps):
    AdmissionPage = apps.get_model('admission', 'AdmissionPage')
    AdmissionPaymentMethod = apps.get_model('admission', 'AdmissionPaymentMethod')

    for page in AdmissionPage.objects.all():
        changed = []
        if not (page.payment_methods_title or '').strip():
            page.payment_methods_title = PAYMENT_METHODS_TITLE['ru']
            changed.append('payment_methods_title')
        for lang in LANGS:
            attr = f'payment_methods_title_{lang}'
            if not (getattr(page, attr, None) or '').strip():
                setattr(page, attr, PAYMENT_METHODS_TITLE[lang])
                changed.append(attr)
        if changed:
            page.save(update_fields=changed)

        if AdmissionPaymentMethod.objects.filter(page=page).exists():
            continue
        for order, method in enumerate(PAYMENT_METHODS, start=1):
            AdmissionPaymentMethod.objects.create(
                page=page,
                order=order,
                text=method['ru'],
                text_ru=method['ru'],
                text_kk=method['kk'],
                text_en=method['en'],
            )


def _rebuild_pricing(apps):
    AdmissionVariant = apps.get_model('admission', 'AdmissionVariant')
    AdmissionPricingPlan = apps.get_model('admission', 'AdmissionPricingPlan')

    for variant in AdmissionVariant.objects.all():
        plans = list(
            AdmissionPricingPlan.objects.filter(variant=variant).order_by('order', 'pk')
        )
        if plans and any(_is_legacy_plan(p) for p in plans):
            best = next((p for p in plans if p.highlight == 'best'), None)
            icon = (best.icon_svg if best and best.icon_svg else None) \
                or next((p.icon_svg for p in plans if p.icon_svg), None) \
                or ICON_PRICE_STAR
            AdmissionPricingPlan.objects.filter(variant=variant).delete()
            AdmissionPricingPlan.objects.create(
                variant=variant,
                order=1,
                highlight='best',
                icon_svg=icon,
                label=PLAN_LABEL['ru'],
                label_ru=PLAN_LABEL['ru'],
                label_kk=PLAN_LABEL['kk'],
                label_en=PLAN_LABEL['en'],
                price_value=PLAN_PRICE_VALUE,
                price_currency=PLAN_CURRENCY,
                note=PLAN_NOTE['ru'],
                note_ru=PLAN_NOTE['ru'],
                note_kk=PLAN_NOTE['kk'],
                note_en=PLAN_NOTE['en'],
            )

        changed = []
        for lang, pairs in LEAD_REPLACEMENTS.items():
            attr = f'pricing_lead_{lang}'
            value = getattr(variant, attr, None) or ''
            new_value = value
            for old, new in pairs:
                new_value = new_value.replace(old, new)
            if new_value != value:
                setattr(variant, attr, new_value)
                changed.append(attr)
                if lang == 'ru':
                    variant.pricing_lead = new_value
                    changed.append('pricing_lead')
        if changed:
            variant.save(update_fields=changed)


def forwards(apps, schema_editor):
    _remove_kz_7_11(apps)
    _seed_payment_methods(apps)
    _rebuild_pricing(apps)


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0016_payment_methods'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
