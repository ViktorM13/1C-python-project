import requests
from datetime import datetime, timedelta
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        profession_keywords = [
            '1с разработчик', '1c разработчик',
            '1с', '1c', '1 c', '1 с'
        ]
        query = ' OR '.join(profession_keywords)
        date_from = (datetime.utcnow() - timedelta(days=1)).isoformat() + 'Z'

        params = {
            'text': query,
            'date_from': date_from,
            'per_page': 10,
            'order_by': 'publication_time',
        }

        resp = requests.get('https://api.hh.ru/vacancies', params=params)
        resp.raise_for_status()
        items = resp.json().get('items', [])

        jobs = []
        for item in items:
            detail = requests.get(item['url'])
            detail.raise_for_status()
            d = detail.json()

            salary_data = d.get('salary') or {}
            salary_from = salary_data.get('from')
            salary_to   = salary_data.get('to')
            salary      = salary_from or salary_to or '—'
            currency    = salary_data.get('currency') or ''

            raw_dt = d.get('published_at', '')
            if '+' in raw_dt:
                raw_dt = raw_dt.split('+')[0]
            raw_dt = raw_dt.rstrip('Z')
            try:
                dt = datetime.fromisoformat(raw_dt)
                published_at = dt.strftime('%Y-%m-%d %H:%M')
            except ValueError:
                published_at = raw_dt

            jobs.append({
                'title':        d.get('name', '—'),
                'description':  d.get('description', '').replace('<highlighttext>', '').replace('</highlighttext>', ''),
                'skills':       ', '.join([s.get('name') for s in d.get('key_skills', [])]),
                'company':      d.get('employer', {}).get('name', '—'),
                'salary':       salary,
                'currency':     currency,
                'region':       d.get('area', {}).get('name', '—'),
                'published_at': published_at,
                'url':          d.get('alternate_url', '#'),
            })

        context['latest_jobs'] = jobs
        return context