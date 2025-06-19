import os
import shutil
from pathlib import Path
import requests
import pandas as pd
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET

from django.conf import settings
from django.core.management.base import BaseCommand

from stats.models import DemandStatistic

CBR_URL = "https://www.cbr.ru/scripts/XML_daily.asp?date_req={date}"
KEYWORDS = ['1с разработчик','1c разработчик','1с','1c','1 c','1 с']

class CBRCache:
    def __init__(self):
        self.cache = {}
    def get(self, date_obj):
        key = (date_obj.year, date_obj.month)
        if key in self.cache:
            return self.cache[key]
        ds = date_obj.strftime("01/%m/%Y")
        r = requests.get(CBR_URL.format(date=ds), timeout=5); r.raise_for_status()
        tree = ET.fromstring(r.content)
        rates = {'RUR':1.0}
        for v in tree.findall('Valute'):
            code = v.find('CharCode').text
            nom  = int(v.find('Nominal').text)
            val  = float(v.find('Value').text.replace(',','.'))
            rates[code] = val/nom
        self.cache[key] = rates
        return rates

def to_rub(row, cache):
    frm, to_ = row.salary_from, row.salary_to
    if pd.isna(frm) and pd.isna(to_):
        return None
    avg = frm if pd.isna(to_) else to_ if pd.isna(frm) else (frm+to_)/2
    cur = row.salary_currency or 'RUR'
    pub = row.published_at.replace(day=1).date()
    rate = cache.get(pub).get(cur, 1.0)
    return avg * rate

class Command(BaseCommand):
    help = 'Импортирует статистику «Востребованность» для 1С‑разработчика'

    def handle(self, *args, **opts):
        base = Path(settings.BASE_DIR)
        csv_f = base / 'data' / 'vacancies_2024.csv'
        if not csv_f.exists():
            self.stderr.write(f"CSV не найден: {csv_f}")
            return

        # Чистим старые графики
        charts_dir = base / 'media' / 'statistics' / 'demand'
        if charts_dir.exists():
            shutil.rmtree(charts_dir)
        charts_dir.mkdir(parents=True, exist_ok=True)

        # Читаем данные
        df = pd.read_csv(csv_f, dtype={'key_skills': str}, low_memory=False)
        df['published_at'] = pd.to_datetime(df['published_at'], errors='coerce', utc=True)
        df = df.dropna(subset=['published_at'])
        mask = df['name'].str.lower().str.contains('|'.join(KEYWORDS))
        df = df[mask].copy()
        df['year'] = df['published_at'].dt.year

        # Конвертация в рубли
        cache = CBRCache()
        df['salary_rub'] = df.apply(lambda r: to_rub(r, cache), axis=1)
        df['salary_rub'] = pd.to_numeric(df['salary_rub'], errors='coerce')
        df = df.dropna(subset=['salary_rub'])
        df = df[df['salary_rub'] <= 10_000_000]

        # 1. Динамика уровня зарплат по годам
        ts = df.groupby('year')['salary_rub'].mean().round()
        html = ts.reset_index().to_html(index=False, float_format='%.0f', classes='table table-striped')
        fig, ax = plt.subplots()
        ax.plot(ts.index, ts.values, marker='o')
        ax.set(title='Динамика зарплат 1С‑разработчика по годам', xlabel='Год', ylabel='Средняя зарплата, ₽')
        ax.grid(True, linestyle='--', alpha=0.6)
        fig.savefig(charts_dir / 'demand_salary_trend.png', bbox_inches='tight')
        plt.close(fig)
        DemandStatistic.objects.update_or_create(
            name='demand_salary_trend',
            defaults={
                'title': 'Динамика зарплат 1С‑разработчика по годам',
                'table_html': html,
                'chart_image': 'statistics/demand/demand_salary_trend.png'
            }
        )

        # 2. Динамика количества вакансий по годам
        tc = df.groupby('year').size()
        html2 = tc.reset_index(name='vacancy_count').to_html(index=False, classes='table table-striped')
        fig, ax = plt.subplots()
        ax.bar(tc.index, tc.values)
        ax.set(title='Динамика количества вакансий 1С‑разработчика по годам', xlabel='Год', ylabel='Число вакансий')
        ax.grid(True, linestyle='--', alpha=0.6)
        fig.savefig(charts_dir / 'demand_count_trend.png', bbox_inches='tight')
        plt.close(fig)
        DemandStatistic.objects.update_or_create(
            name='demand_count_trend',
            defaults={
                'title': 'Динамика количества вакансий 1С‑разработчика по годам',
                'table_html': html2,
                'chart_image': 'statistics/demand/demand_count_trend.png'
            }
        )

        self.stdout.write(self.style.SUCCESS('«Востребованность» обновлена.'))
