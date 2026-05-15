from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import RedirectView, TemplateView

from .models import AdmissionPage, AdmissionVariant, Department, GradeGroup


DEFAULT_DEPARTMENT_SLUG = 'ru'


def _default_grade_for(department: Department) -> GradeGroup | None:
    """Первая (по order) группа классов, доступная для отделения.
    Доступность определяется наличием хотя бы одного AdmissionVariant."""
    return (
        GradeGroup.objects
        .filter(variants__department=department)
        .order_by('order', 'pk')
        .first()
    )


class AdmissionRootRedirectView(RedirectView):
    """`/<lang>/<region>/admission/` → default department + default grade."""

    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        department = (
            Department.objects.filter(slug=DEFAULT_DEPARTMENT_SLUG).first()
            or Department.objects.order_by('order').first()
        )
        if department is None:
            raise Http404('No departments configured')
        grade = _default_grade_for(department)
        if grade is None:
            raise Http404('No grade groups for default department')
        return f'./{department.slug}/grade-{grade.slug}/'


class AdmissionDepartmentRedirectView(RedirectView):
    """`/<lang>/<region>/admission/<dept>/` → его дефолтный класс (первый по order)."""

    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        department = get_object_or_404(Department, slug=kwargs['department_slug'])
        grade = _default_grade_for(department)
        if grade is None:
            raise Http404('No grade groups for this department')
        return f'./grade-{grade.slug}/'


class AdmissionView(TemplateView):
    template_name = 'admission/detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        department_slug = kwargs['department_slug']
        grade_slug = kwargs['grade_slug']

        page = get_object_or_404(AdmissionPage, region=self.request.region)
        department = get_object_or_404(Department, slug=department_slug)
        grade = get_object_or_404(GradeGroup, slug=grade_slug)
        variant = get_object_or_404(
            AdmissionVariant.objects.select_related('page__region', 'department', 'grade')
            .prefetch_related('testing_features', 'pricing_plans'),
            page=page, department=department, grade=grade,
        )

        # Доступные группы классов для текущего отделения — определяет
        # содержимое второго dropdown'а в hero.
        available_grades = list(
            GradeGroup.objects
            .filter(variants__page=page, variants__department=department)
            .distinct()
            .order_by('order', 'pk')
        )
        all_departments = list(Department.objects.order_by('order'))

        ctx.update({
            'page': page,
            'variant': variant,
            'current_department': department,
            'current_grade': grade,
            'all_departments': all_departments,
            'available_grades': available_grades,
            'testing_features': list(variant.testing_features.all()),
            'pricing_plans': list(variant.pricing_plans.all()),
            'included_items': [i for i in page.included_items.all() if not i.is_excluded],
            'excluded_items': [i for i in page.included_items.all() if i.is_excluded],
            'documents': list(page.documents.all()),
        })
        return ctx
