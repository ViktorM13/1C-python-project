import os
from pathlib import Path
import requests
import pandas as pd
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET

from django.conf import settings
from django.core.management.base import BaseCommand

from stats.models import GeneralStatistic

CBR_URL = "https://www.cbr.ru/scripts/XML_daily.asp?date_req={date}"


def collect_exchange_rates(dates):
    cache = {}
    for date in dates:
        key = (date.year, date.month)
        if key in cache:
            continue
        try:
            date_str = date.strftime("%d/%m/%Y")
            resp = requests.get(CBR_URL.format(date=date_str), timeout=5)
            resp.raise_for_status()
            tree = ET.fromstring(resp.content)
            rates = {'RUR': 1.0}
            for valute in tree.findall('Valute'):
                char_code = valute.find('CharCode').text
                nominal = int(valute.find('Nominal').text)
                value_str = valute.find('Value').text.replace(',', '.')
                rates[char_code] = float(value_str) / nominal
            cache[key] = rates
        except Exception as e:
            print(f"[WARNING] Error fetching rates for {date}: {e}")
            cache[key] = {'RUR': 1.0}
    return cache


def salary_to_rub(row, cache):
    avg = pd.Series([row.salary_from, row.salary_to]).mean()
    if pd.isna(avg):
        return pd.NA
    first_of_month = row.published_at.replace(day=1).date()
    rates = cache.get((first_of_month.year, first_of_month.month), {'RUR': 1.0})
    return avg * rates.get(row.salary_currency, 1.0)


class Command(BaseCommand):
    help = 'Импортирует CSV и генерирует статистику с курсами ЦБ'

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR)
        csv_path = base_dir / 'data' / 'vacancies_2024.csv'
        if not csv_path.exists():
            self.stderr.write(f"CSV not found: {csv_path}")
            return

        # 1. Читаем CSV и готовим даты
        df = pd.read_csv(csv_path, dtype={'key_skills': str}, low_memory=False)
        df['published_at'] = pd.to_datetime(df['published_at'], errors='coerce', utc=True)
        df = df.dropna(subset=['published_at'])
        # Убираем tzinfo, чтобы не было предупреждений
        df['published_at'] = df['published_at'].dt.tz_localize(None)
        df['year'] = df['published_at'].dt.year

        # Явно берём первый день каждого месяца
        df['pub_month'] = df['published_at'].apply(lambda dt: dt.replace(day=1).date())
        unique_dates = df['pub_month'].unique()

        # 2. Скачиваем курсы лишь по уникальным датам
        cbr_cache = collect_exchange_rates(unique_dates)

        # 3. Переводим зарплаты в рубли
        df['salary_rub'] = df.apply(lambda r: salary_to_rub(r, cbr_cache), axis=1)
        df['salary_rub'] = pd.to_numeric(df['salary_rub'], errors='coerce')
        df = df.dropna(subset=['salary_rub'])
        df = df[df['salary_rub'] <= 10_000_000]

        # 4. Папка для графиков
        media_charts = base_dir / 'media' / 'statistics' / 'charts'
        media_charts.mkdir(parents=True, exist_ok=True)

        # === Блок 1: Динамика зарплат ===
        ts_salary = df.groupby('year')['salary_rub'].mean().round()
        html_salary = ts_salary.reset_index().to_html(
            index=False, float_format='%.0f', classes='table table-striped')
        fig, ax = plt.subplots()
        ax.plot(ts_salary.index, ts_salary.values, marker='o')
        ax.set_title('Динамика уровня зарплат по годам')
        ax.set_xlabel('Год')
        ax.set_ylabel('Средняя зарплата, ₽')
        ax.grid(True, linestyle='--', alpha=0.6)
        fig.savefig(media_charts / 'salary_trend.png', bbox_inches='tight')
        plt.close(fig)
        GeneralStatistic.objects.update_or_create(
            name='salary_trend',
            defaults={
                'title': 'Динамика уровня зарплат по годам',
                'table_html': html_salary,
                'chart_image': 'statistics/charts/salary_trend.png',
            }
        )

        # === Блок 2: Количество вакансий ===
        ts_count = df.groupby('year').size()
        html_count = ts_count.reset_index(name='vacancy_count').to_html(
            index=False, classes='table table-striped')
        fig, ax = plt.subplots()
        ax.bar(ts_count.index, ts_count.values)
        ax.set_title('Динамика количества вакансий по годам')
        ax.set_xlabel('Год')
        ax.set_ylabel('Количество вакансий')
        ax.grid(True, linestyle='--', alpha=0.6)
        fig.savefig(media_charts / 'count_trend.png', bbox_inches='tight')
        plt.close(fig)
        GeneralStatistic.objects.update_or_create(
            name='count_trend',
            defaults={
                'title': 'Динамика количества вакансий по годам',
                'table_html': html_count,
                'chart_image': 'statistics/charts/count_trend.png',
            }
        )

        # === Блок 3: Зарплаты по городам ===
        city_salary = df.groupby('area_name')['salary_rub'] \
            .mean().round().sort_values(ascending=False).head(20)
        html_city_sal = city_salary.reset_index().to_html(
            index=False, float_format='%.0f', classes='table table-striped')
        fig, ax = plt.subplots(figsize=(6, 8))
        ax.barh(city_salary.index, city_salary.values)
        ax.invert_yaxis()
        ax.set_title('Уровень зарплат по городам (ТОП-20)')
        ax.set_xlabel('Средняя зарплата, млн. ₽')
        ax.grid(True, linestyle='--', alpha=0.6, axis='x')
        fig.savefig(media_charts / 'city_salary.png', bbox_inches='tight')
        plt.close(fig)
        GeneralStatistic.objects.update_or_create(
            name='city_salary',
            defaults={
                'title': 'Уровень зарплат по городам (ТОП-20)',
                'table_html': html_city_sal,
                'chart_image': 'statistics/charts/city_salary.png',
            }
        )

        # === Блок 4: Доля вакансий по городам ===
        city_count = df.groupby('area_name').size() \
            .sort_values(ascending=False).head(20)
        total = city_count.sum()
        city_share = (city_count / total * 100).round(2)
        html_city_share = city_share.reset_index(name='share').to_html(
            index=False, float_format='%.2f', classes='table table-striped')
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(city_share.values, labels=city_share.index, autopct='%1.1f%%')
        ax.set_title('Доля вакансий по городам (ТОП-20)')
        fig.savefig(media_charts / 'city_share.png', bbox_inches='tight')
        plt.close(fig)
        GeneralStatistic.objects.update_or_create(
            name='city_share',
            defaults={
                'title': 'Доля вакансий по городам (ТОП-20)',
                'table_html': html_city_share,
                'chart_image': 'statistics/charts/city_share.png',
            }
        )

        # === Блок 5: ТОП-20 навыков по годам ===
        df['key_skills'] = df['key_skills'].replace('', pd.NA)
        df_sk = df.dropna(subset=['key_skills']).copy()
        # Нормализация: split + strip + lower
        df_sk['skills_list'] = df_sk['key_skills'] \
            .str.split(',') \
            .apply(lambda skills: [s.strip().lower() for s in skills if s.strip()])

        records = []
        skill_counts = {}
        for _, row in df_sk.iterrows():
            year = row['year']
            for norm in row['skills_list']:
                records.append((year, norm))
                skill_counts[norm] = skill_counts.get(norm, 0) + 1

        top_skills = sorted(skill_counts, key=skill_counts.get, reverse=True)[:20]
        skill_df = pd.DataFrame(records, columns=['year', 'skill'])
        filtered = skill_df[skill_df['skill'].isin(top_skills)]
        pivot = filtered.pivot_table(
            index='year', columns='skill', aggfunc='size', fill_value=0)

        html_skills = pivot.reset_index().to_html(
            index=False, classes='table table-striped')
        fig, ax = plt.subplots(figsize=(12, 6))
        for skill in pivot.columns:
            ax.plot(pivot.index, pivot[skill], label=skill.title())
        ax.set_title('ТОП-20 навыков по годам')
        ax.set_xlabel('Год')
        ax.set_ylabel('Количество упоминаний')
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
        fig.tight_layout()
        fig.savefig(media_charts / 'skills_by_year.png', bbox_inches='tight')
        plt.close(fig)
        GeneralStatistic.objects.update_or_create(
            name='skills_by_year',
            defaults={
                'title': 'ТОП-20 навыков по годам',
                'table_html': html_skills,
                'chart_image': 'statistics/charts/skills_by_year.png',
            }
        )

        self.stdout.write(self.style.SUCCESS(
            'Все блоки статистики успешно созданы/обновлены.'))
