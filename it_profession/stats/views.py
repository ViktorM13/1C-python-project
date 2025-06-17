from django.views.generic import TemplateView
from .models import GeneralStatistic

class GeneralStatsView(TemplateView):
    template_name = 'stats/general_stats.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['blocks'] = GeneralStatistic.objects.all()
        return ctx
