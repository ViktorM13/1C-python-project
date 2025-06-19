from django.views.generic import TemplateView
from .models import GeneralStatistic
from .models import DemandStatistic

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