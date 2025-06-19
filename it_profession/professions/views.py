from django.utils import timezone
from datetime import timedelta
from django.views.generic import TemplateView
from .models import HHVacancy
from .models import PageContent

class IndexView(TemplateView):
    template_name = 'professions/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page'] = PageContent.objects.get(slug='home')
        return ctx

class GeographyView(TemplateView):
    template_name = 'professions/geography.html'

class SkillsView(TemplateView):
    template_name = 'professions/skills.html'

class LatestJobsView(TemplateView):
    template_name = 'professions/latest_jobs.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        since = timezone.now() - timedelta(hours=24)
        ctx['vacancies'] = (
            HHVacancy.objects
            .filter(published_at__gte=since)
            .order_by('-published_at')[:10]
        )
        return ctx