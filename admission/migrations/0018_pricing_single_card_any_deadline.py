"""Досворачивание прайса в одну карту там, где 0017 не сработала.

0017 пересобирала прайс-карты только при маркере «1 июня» — на проде в Актау
менеджер к тому моменту уже вбил свои цены со сроком «1 июля»
(«100% до 1 июля» 1 710 000 / «Ежеквартально» 1 800 000 / «Годовая оплата»
1 980 000), и варианты остались с тремя колонками. ТЗ школы — убрать колонки
везде, поэтому здесь правило шире: любой вариант, у которого больше одной
карты ИЛИ карта с маркером срока/рассрочки (июня/июля/маусым/шілде/June/July,
«Ежеквартально», «Годовая оплата» и их kk/en), сворачивается в одну карту
«Стоимость обучения / <цена годовой оплаты> ₸ / За 2026–2027 учебный год».

Цена берётся из карты «Годовая оплата» (annual payment / жылдық төлем) того же
варианта, иначе — из последней по order; форматируется «1 980 000». Валюта и
иконка — с существующих карт. Способы оплаты (`AdmissionPaymentMethod`) уже
посеяны 0017 per region и здесь не трогаются.

Данные inline, идемпотентно, reverse — no-op.
"""
import re

from django.db import migrations


LANGS = ('ru', 'kk', 'en')

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

# Маркеры устаревшего прайса (сравнение после нормализации пробелов и регистра).
LEGACY_MARKERS = (
    '1 июня', '1 июля', '1 маусым', '1 шілде',
    'june 1', 'july 1', '1 june', '1 july',
    'ежеквартально', 'quarterly', 'тоқсан сайын', 'траншқа бөліп',
    'годовая оплата', 'annual payment', 'жылдық төлем',
)
ANNUAL_MARKERS = ('годовая оплата', 'annual payment', 'жылдық төлем')

LEAD_REPLACEMENTS = {
    'ru': [('После выбора тарифа', 'После выбора способа оплаты')],
    'kk': [('Тарифті таңдағаннан кейін', 'Төлем тәсілін таңдағаннан кейін')],
    'en': [('a plan', 'a payment option')],
}


def _norm(value):
    return (value or '').replace('\xa0', ' ').replace(' ', ' ').lower()


def _plan_texts(plan):
    for lang in LANGS:
        for field in ('label', 'note'):
            yield _norm(getattr(plan, f'{field}_{lang}', None))


def _is_legacy_plan(plan):
    return any(marker in text for text in _plan_texts(plan) for marker in LEGACY_MARKERS)


def _is_annual_plan(plan):
    return any(marker in text for text in _plan_texts(plan) for marker in ANNUAL_MARKERS)


def _format_price(raw):
    """'1980000' / '1 980 000' / '1,980,000' → '1 980 000'. Нечисловое — как есть."""
    digits = re.sub(r'\D', '', raw or '')
    if not digits:
        return (raw or '').strip()
    groups = []
    while digits:
        groups.insert(0, digits[-3:])
        digits = digits[:-3]
    return ' '.join(groups)


def _pick_source(plans):
    """Карта, из которой берём цену: «Годовая оплата», иначе последняя по order."""
    annual = [p for p in plans if _is_annual_plan(p)]
    if annual:
        return annual[-1]
    return plans[-1]


def _needs_rebuild(plans):
    return len(plans) > 1 or any(_is_legacy_plan(p) for p in plans)


def _rebuild_variant(AdmissionPricingPlan, variant, plans):
    source = _pick_source(plans)
    best = next((p for p in plans if p.highlight == 'best'), None)
    icon = (
        (best.icon_svg if best and best.icon_svg else None)
        or next((p.icon_svg for p in plans if p.icon_svg), None)
        or ''
    )
    price_value = _format_price(source.price_value)
    currency = (source.price_currency or '₸').strip() or '₸'

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
        price_value=price_value,
        price_currency=currency,
        note=PLAN_NOTE['ru'],
        note_ru=PLAN_NOTE['ru'],
        note_kk=PLAN_NOTE['kk'],
        note_en=PLAN_NOTE['en'],
    )
    return price_value


def forwards(apps, schema_editor):
    AdmissionVariant = apps.get_model('admission', 'AdmissionVariant')
    AdmissionPricingPlan = apps.get_model('admission', 'AdmissionPricingPlan')

    for variant in AdmissionVariant.objects.all():
        plans = list(
            AdmissionPricingPlan.objects.filter(variant=variant).order_by('order', 'pk')
        )
        if plans and _needs_rebuild(plans):
            _rebuild_variant(AdmissionPricingPlan, variant, plans)

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


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0017_pricing_single_card_payment_methods'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
