"""Lead edit-форма. Контактные поля (name/phone/city/origin/title) — read-only
в шаблоне; форма управляет только статусом, категорией и заметкой менеджера.
"""

from django import forms

from feedback.models import Lead


class LeadEditForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ('status', 'category', 'manager_note')
        widgets = {
            'manager_note': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Что по звонку, договорённости, причина отказа.',
            }),
        }
