from django.views.generic import TemplateView

class IndexView(TemplateView):
    template_name = 'professions/index.html'

class GeneralStatsView(TemplateView):
    template_name = 'professions/general_stats.html'

class DemandView(TemplateView):
    template_name = 'professions/demand.html'

class GeographyView(TemplateView):
    template_name = 'professions/geography.html'

class SkillsView(TemplateView):
    template_name = 'professions/skills.html'

class LatestJobsView(TemplateView):
    template_name = 'professions/latest_jobs.html'
