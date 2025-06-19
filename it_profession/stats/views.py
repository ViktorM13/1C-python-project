from django.views.generic import TemplateView
from .models import GeneralStatistic, DemandStatistic, GeographyStatistic, SkillStatistic

class GeneralStatsView(TemplateView):
    template_name = 'stats/general_stats.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['blocks'] = GeneralStatistic.objects.all()
        return ctx

class DemandView(TemplateView):
    template_name = 'stats/demand.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['blocks'] = DemandStatistic.objects.all()
        return ctx

class GeographyView(TemplateView):
    template_name = 'stats/geography.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['blocks'] = GeographyStatistic.objects.all()
        return ctx

class SkillView(TemplateView):
    template_name = 'stats/skills.html'
    def get_context_data(self, **kw):
        ctx = super().get_context_data(**kw)
        ctx['blocks'] = SkillStatistic.objects.all()
        return ctx