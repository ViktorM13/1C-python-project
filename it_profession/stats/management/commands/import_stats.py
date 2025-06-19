import os
from pathlib import Path
import shutil
import requests
import pandas as pd
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET

from django.conf import settings
from django.core.management.base import BaseCommand

from stats.models import GeneralStatistic

CBR_URL = "https://www.cbr.ru/scripts/XML_daily.asp?date_req={date}"
COUNTRIES_FILE = 'data/russian_countries.txt'


def collect_exchange_rates(dates):
    cache = {}
    for date in dates:
        key = (date.year, date.month)
        if key in cache:
            continue
        try:
            date_str = date.strftime("01/%m/%Y")
            resp = requests.get(CBR_URL.format(date=date_str), timeout=5)
            resp.raise_for_status()
            tree = ET.fromstring(resp.content)
            rates = {'RUR': (1.0, 1)}
            for valute in tree.findall('Valute'):
                code = valute.find('CharCode').text
                nominal = int(valute.find('Nominal').text)
                value = float(valute.find('Value').text.replace(',', '.'))
                rates[code] = (value, nominal)
            cache[key] = rates
        except Exception:
            cache[key] = {'RUR': (1.0, 1)}
    return cache


def convert_salary_to_rub(row, cache):
    frm, to_ = row.salary_from, row.salary_to
    if pd.isna(frm) and pd.isna(to_): return pd.NA
    if (not pd.isna(frm) and frm < 0) or (not pd.isna(to_) and to_ < 0): return pd.NA
    avg = frm if pd.isna(to_) else to_ if pd.isna(frm) else (frm + to_) / 2
    cur = row.salary_currency
    if cur == 'BYR': avg, cur = avg / 10000, 'BYN'
    if pd.isna(cur) or cur == 'RUR': return avg
    pub = row.published_at
    key = (pub.year, pub.month)
    rate, nominal = cache.get(key, {}).get(cur, (None, None))
    if not rate or not nominal: return pd.NA
    return avg * rate / nominal


class Command(BaseCommand):
    help = 'Импортирует CSV и генерирует статистику с курсами ЦБ (исключая страны)'

    def handle(self, *args, **options):
        base = Path(settings.BASE_DIR)
        GeneralStatistic.objects.all().delete()
        charts = base / 'media' / 'statistics' / 'charts'
        if charts.exists(): shutil.rmtree(charts)
        charts.mkdir(parents=True, exist_ok=True)

        countries_path = base / COUNTRIES_FILE
        with open(countries_path, encoding='utf-8') as f:
            COUNTRIES = {line.strip() for line in f if line.strip()}

        csv_file = base / 'data' / 'vacancies_2024.csv'
        if not csv_file.exists():
            self.stderr.write(f"CSV not found: {csv_file}")
            return
        df = pd.read_csv(csv_file, dtype={'key_skills': str}, low_memory=False)
        df['published_at'] = pd.to_datetime(df['published_at'], errors='coerce', utc=True)
        df.dropna(subset=['published_at'], inplace=True)
        df['published_at'] = df['published_at'].dt.tz_localize(None)

        df = df[~df['area_name'].isin(COUNTRIES)]
        df['year'] = df['published_at'].dt.year

        df['pub_month'] = df['published_at'].apply(lambda d: d.replace(day=1).date())
        cache = collect_exchange_rates(df['pub_month'].unique())

        df['salary_rub'] = df.apply(lambda r: convert_salary_to_rub(r, cache), axis=1)
        df['salary_rub'] = pd.to_numeric(df['salary_rub'], errors='coerce')
        df.dropna(subset=['salary_rub'], inplace=True)
        df = df[df['salary_rub'] <= 10_000_000]

        ts = df.groupby('year')['salary_rub'].mean().round()
        html = ts.reset_index().to_html(index=False, float_format='%.0f', classes='table table-striped')
        fig,ax = plt.subplots(); ax.plot(ts.index,ts.values,marker='o'); ax.set(title='Динамика уровня зарплат по годам',xlabel='Год',ylabel='Средняя зарплата, ₽'); ax.grid(True, linestyle='--', alpha=0.6)
        fig.savefig(charts/'salary_trend.png',bbox_inches='tight'); plt.close(fig)
        GeneralStatistic.objects.create(name='salary_trend', title='Динамика уровня зарплат по годам', table_html=html, chart_image='statistics/charts/salary_trend.png')

        tc = df.groupby('year').size()
        html = tc.reset_index(name='vacancy_count').to_html(index=False,classes='table table-striped')
        fig,ax=plt.subplots(); ax.bar(tc.index,tc.values); ax.set(title='Динамика количества вакансий по годам',xlabel='Год',ylabel='Количество вакансий'); ax.grid(True, linestyle='--', alpha=0.6)
        fig.savefig(charts/'count_trend.png',bbox_inches='tight'); plt.close(fig)
        GeneralStatistic.objects.create(name='count_trend', title='Динамика количества вакансий по годам', table_html=html, chart_image='statistics/charts/count_trend.png')

        cs = df.groupby('area_name')['salary_rub'].mean().round().nlargest(20)
        html = cs.reset_index().to_html(index=False,float_format='%.0f',classes='table table-striped')
        fig,ax=plt.subplots(figsize=(6,8)); ax.barh(cs.index,cs.values); ax.invert_yaxis(); ax.set(title='Уровень зарплат по городам (ТОП-20)',xlabel='Средняя зарплата, ₽'); ax.grid(True, linestyle='--', alpha=0.6, axis='x')
        fig.savefig(charts/'city_salary.png',bbox_inches='tight'); plt.close(fig)
        GeneralStatistic.objects.create(name='city_salary', title='Уровень зарплат по городам (ТОП-20)', table_html=html, chart_image='statistics/charts/city_salary.png')

        vc = df['area_name'].value_counts().nlargest(20)
        share = (vc/vc.sum()*100).round(2)
        html = share.reset_index(name='share').to_html(index=False, float_format='%.2f',classes='table table-striped')
        fig,ax=plt.subplots(figsize=(8,8)); ax.pie(share.values,labels=share.index,autopct='%1.1f%%'); ax.set_title('Доля вакансий по городам (ТОП-20)')
        fig.savefig(charts/'city_share.png',bbox_inches='tight'); plt.close(fig)
        GeneralStatistic.objects.create(name='city_share',title='Доля вакансий по городам (ТОП-20)', table_html=html, chart_image='statistics/charts/city_share.png')

        df['key_skills']=df['key_skills'].replace('',pd.NA)
        sk=df.dropna(subset=['key_skills']).copy(); sk['skills_list']=sk['key_skills'].str.split('\n').apply(lambda lst:[s.strip().lower() for s in lst if s.strip()])
        from collections import Counter; rec=[]
        for _,r in sk.iterrows(): rec+=[(r['year'],s) for s in r['skills_list']]
        sdf=pd.DataFrame(rec,columns=['year','skill']); top=[s for s,_ in Counter(sdf['skill']).most_common(20)]
        piv=sdf[sdf['skill'].isin(top)].pivot_table(index='year',columns='skill',aggfunc='size',fill_value=0)
        html = piv.reset_index().to_html(index=False,classes='table table-striped')
        fig,ax=plt.subplots(figsize=(12,6)); [ax.plot(piv.index,piv[c],label=c.title()) for c in piv.columns]; ax.set(title='ТОП-20 навыков по годам',xlabel='Год',ylabel='Количество упоминаний'); ax.grid(True, linestyle='--', alpha=0.6); ax.legend(loc='center left',bbox_to_anchor=(1,0.5)); fig.tight_layout()
        fig.savefig(charts/'skills_by_year.png',bbox_inches='tight'); plt.close(fig)
        GeneralStatistic.objects.create(name='skills_by_year',title='ТОП-20 навыков по годам',table_html=html,chart_image='statistics/charts/skills_by_year.png')

        self.stdout.write(self.style.SUCCESS('Статистика успешно обновлена.'))
