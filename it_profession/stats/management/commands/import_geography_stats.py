import shutil
from pathlib import Path
import requests
import pandas as pd
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET

from django.conf import settings
from django.core.management.base import BaseCommand

from stats.models import GeographyStatistic

CBR_URL         = "https://www.cbr.ru/scripts/XML_daily.asp?date_req={date}"
KEYWORDS        = ['1с разработчик','1c разработчик','1с','1c','1 c','1 с']
COUNTRIES_FILE  = 'data/russian_countries.txt'

class CBRCache:
    def __init__(self):
        self.cache = {}
    def get(self, date_obj):
        key = (date_obj.year, date_obj.month)
        if key in self.cache:
            return self.cache[key]
        ds   = date_obj.strftime("01/%m/%Y")
        resp = requests.get(CBR_URL.format(date=ds), timeout=5)
        resp.raise_for_status()
        tree = ET.fromstring(resp.content)
        rates = {'RUR': 1.0}
        for v in tree.findall('Valute'):
            code = v.find('CharCode').text
            nom  = int(v.find('Nominal').text)
            val  = float(v.find('Value').text.replace(',', '.'))
            rates[code] = val / nom
        self.cache[key] = rates
        return rates

def to_rub(row, cache):
    frm, to_ = row.salary_from, row.salary_to
    if pd.isna(frm) and pd.isna(to_):
        return None
    avg = frm if pd.isna(to_) else to_ if pd.isna(frm) else (frm + to_) / 2
    cur = row.salary_currency or 'RUR'
    pub = row.published_at.replace(day=1).date()
    rate = cache.get(pub).get(cur, 1.0)
    return avg * rate

class Command(BaseCommand):
    help = 'Импортирует статистику «География» для 1С‑разработчика'

    def handle(self, *args, **opts):
        base           = Path(settings.BASE_DIR)
        csv_f          = base / 'data' / 'vacancies_2024.csv'
        charts         = base / 'media' / 'statistics' / 'geography'
        countries_path = base / COUNTRIES_FILE

        if charts.exists():
            shutil.rmtree(charts)
        charts.mkdir(parents=True, exist_ok=True)
        GeographyStatistic.objects.all().delete()

        if countries_path.exists():
            with open(countries_path, encoding='utf-8') as f:
                RUS_COUNTRIES = {line.strip() for line in f if line.strip()}
        else:
            RUS_COUNTRIES = set()

        df = pd.read_csv(csv_f, dtype={'key_skills': str}, low_memory=False)
        df['published_at'] = pd.to_datetime(df['published_at'], errors='coerce', utc=True)
        df = df.dropna(subset=['published_at'])
        mask = df['name'].str.lower().str.contains('|'.join(KEYWORDS))
        df = df[mask].copy()
        df = df[~df['area_name'].isin(RUS_COUNTRIES)]
        df['year'] = df['published_at'].dt.year

        cache = CBRCache()
        df['salary_rub'] = df.apply(lambda r: to_rub(r, cache), axis=1)
        df['salary_rub'] = pd.to_numeric(df['salary_rub'], errors='coerce')
        df = df.dropna(subset=['salary_rub'])
        df = df[df['salary_rub'] <= 10_000_000]

        city_sal = (
            df.groupby('area_name')['salary_rub']
              .mean()
              .round()
              .nlargest(20)
        )
        table1 = city_sal.reset_index().rename(columns={
            'area_name': 'Город',
            'salary_rub':'Средняя зарплата (₽)'
        })
        html1 = table1.to_html(
            index=False,
            float_format='%.0f',
            classes='table table-striped',
            justify='left'
        )
        fig, ax = plt.subplots(figsize=(6, 8))
        ax.barh(city_sal.index, city_sal.values)
        ax.invert_yaxis()
        ax.set(
            title='Уровень зарплат по городам (ТОП-20)',
            xlabel='Средняя зарплата, ₽'
        )
        ax.grid(True, linestyle='--', alpha=0.6, axis='x')
        fig.savefig(charts / 'geo_salary.png', bbox_inches='tight')
        plt.close(fig)
        GeographyStatistic.objects.create(
            name='geo_salary',
            title='Уровень зарплат по городам (ТОП-20)',
            table_html=html1,
            chart_image='statistics/geography/geo_salary.png'
        )

        city_cnt = df['area_name'].value_counts().nlargest(20)
        share    = (city_cnt / city_cnt.sum() * 100).round(2)
        table2 = share.reset_index(name='Доля (%)').rename(columns={
            'area_name': 'Город'
        })
        html2 = table2.to_html(
            index=False,
            float_format='%.2f',
            classes='table table-striped',
            justify='left'
        )
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(share.values, labels=share.index, autopct=None)
        ax.set_title('Доля вакансий по городам (ТОП-20)')
        fig.savefig(charts / 'geo_share.png', bbox_inches='tight')
        plt.close(fig)
        GeographyStatistic.objects.create(
            name='geo_share',
            title='Доля вакансий по городам (ТОП-20)',
            table_html=html2,
            chart_image='statistics/geography/geo_share.png'
        )

        self.stdout.write(self.style.SUCCESS('«География» обновлена.'))
