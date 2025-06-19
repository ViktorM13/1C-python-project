import shutil
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from collections import Counter, OrderedDict

from django.conf import settings
from django.core.management.base import BaseCommand

from stats.models import SkillStatistic

KEYWORDS = ['1с разработчик', '1c разработчик', '1с', '1c', '1 c', '1 с']

class Command(BaseCommand):
    help = 'Импортирует ТОП‑20 навыков по годам для 1С‑разработчика'

    def handle(self, *args, **opts):
        base   = Path(settings.BASE_DIR)
        csv_f  = base / 'data' / 'vacancies_2024.csv'
        charts = base / 'media' / 'statistics' / 'skills'

        if charts.exists():
            shutil.rmtree(charts)
        charts.mkdir(parents=True, exist_ok=True)
        SkillStatistic.objects.all().delete()

        df = pd.read_csv(csv_f, dtype={'key_skills': str}, low_memory=False)
        df['published_at'] = pd.to_datetime(df['published_at'], errors='coerce', utc=True)
        df = df.dropna(subset=['published_at'])
        mask = df['name'].str.lower().str.contains('|'.join(KEYWORDS))
        df = df[mask].copy()
        df['year'] = df['published_at'].dt.year

        df = df.dropna(subset=['key_skills']).copy()
        df['skills_list'] = df['key_skills'].str.split(',') \
            .apply(lambda lst: list({s.strip().lower() for s in lst if s.strip()}))

        records = []
        for _, row in df.iterrows():
            for skill in row['skills_list']:
                records.append((row['year'], skill))
        sdf = pd.DataFrame(records, columns=['year', 'skill'])

        raw_top20 = [s for s, _ in Counter(sdf['skill']).most_common(20)]
        top20 = list(OrderedDict.fromkeys(raw_top20))

        piv = (
            sdf[sdf['skill'].isin(top20)]
            .pivot_table(index='year', columns='skill', aggfunc='size', fill_value=0)
            .reindex(columns=top20, fill_value=0)
        )

        html = piv.reset_index().to_html(index=False, classes='table table-striped')

        fig, ax = plt.subplots(figsize=(12, 6))
        for skill in top20:
            ax.plot(piv.index, piv[skill], label=skill.title())
        ax.set(
            title='ТОП‑20 навыков по годам для 1С‑разработчика',
            xlabel='Год',
            ylabel='Число упоминаний'
        )
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        fig.tight_layout()

        out_path = charts / 'skills_by_year.png'
        fig.savefig(out_path, bbox_inches='tight')
        plt.close(fig)

        SkillStatistic.objects.create(
            name='skills_by_year',
            title='ТОП‑20 навыков по годам',
            table_html=html,
            chart_image=f'statistics/skills/{out_path.name}'
        )

        self.stdout.write(self.style.SUCCESS('«Навыки» успешно обновлены.'))
