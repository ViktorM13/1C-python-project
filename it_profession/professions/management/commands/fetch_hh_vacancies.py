import requests
from datetime import datetime, timedelta, timezone
from django.core.management.base import BaseCommand
from django.utils import timezone as dj_timezone
from professions.models import HHVacancy

class Command(BaseCommand):
    help = 'Загружает последние вакансии 1С-разработчика из HH.ru в базу'

    def handle(self, *args, **options):
        HHVacancy.objects.all().delete()

        keywords = ['1с разработчик', '1c разработчик', '1C разработчик', '1С разработчик','1с', '1c', '1С', '1C']
        query = ' OR '.join(keywords)
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

        for item in items:
            detail = requests.get(item['url'])
            detail.raise_for_status()
            d = detail.json()

            salary_data = d.get('salary') or {}
            salary = salary_data.get('from') or salary_data.get('to') or ''
            currency = salary_data.get('currency') or ''

            raw_dt = d.get('published_at', '').rstrip('Z').split('+')[0]
            naive_dt = datetime.fromisoformat(raw_dt)
            published_at = dj_timezone.make_aware(naive_dt, timezone.utc)

            HHVacancy.objects.create(
                title=d.get('name', ''),
                description=d.get('description', ''),
                skills=', '.join(s.get('name') for s in d.get('key_skills', [])),
                company=d.get('employer', {}).get('name', ''),
                url=d.get('alternate_url', ''),
                salary=salary,
                currency=currency,
                region=d.get('area', {}).get('name', ''),
                published_at=published_at,
            )

        self.stdout.write(self.style.SUCCESS('Вакансии успешно обновлены (старые удалены, новые загружены).'))
