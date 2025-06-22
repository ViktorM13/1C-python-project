import shutil
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import itertools # Добавим для цикличности по стилям линий

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
        df['skills_list'] = (
            df['key_skills']
              .str.split(',')
              .apply(lambda lst: list({s.strip().lower() for s in lst if s.strip()}))
        )

        records = []
        for _, row in df.iterrows():
            for skill in row['skills_list']:
                records.append((row['year'], skill))
        sdf = pd.DataFrame(records, columns=['Год', 'Навык'])

        raw_top20 = [s for s, _ in Counter(sdf['Навык']).most_common(20)]
        top20 = list(OrderedDict.fromkeys(raw_top20))

        piv = (
            sdf[sdf['Навык'].isin(top20)]
            .pivot_table(index='Год', columns='Навык', aggfunc='size', fill_value=0)
            .reindex(columns=top20, fill_value=0)
            .rename_axis(None, axis='columns')
        )

        table = piv.reset_index()
        html = table.to_html(
            index=False,
            classes='table table-striped',
            justify='left'
        )

        # ----- ИЗМЕНЕНИЯ НАЧИНАЮТСЯ ЗДЕСЬ -----

        # Различные стили линий и маркеры
        linestyles = ['-', '--', ':', '-.']
        markers = ['o', 's', 'D', '^', 'v', 'p', 'h', '*', 'X']
        # Используем itertools.cycle, чтобы циклически проходить по стилям/маркерам
        style_cycle = itertools.cycle(linestyles)
        marker_cycle = itertools.cycle(markers)


        fig, ax = plt.subplots(figsize=(18, 12)) # Увеличение размера рисунка (например, 15x8)

        for skill in top20:
            # Применяем различные стили и маркеры
            ax.plot(piv.index, piv[skill], label=skill.title(),
                    linestyle=next(style_cycle), marker=next(marker_cycle), markersize=5) # Добавлен linestyle и marker
        ax.set(
            title='ТОП‑20 навыков по годам для 1С‑разработчика',
            xlabel='Год',
            ylabel='Число упоминаний'
        )
        ax.grid(True, linestyle='--', alpha=0.6)

        # Изменение расположения легенды: вниз, по центру, за пределами графика
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.10),
                  fancybox=True, shadow=True, ncol=5) # ncol=5 для размещения в 5 колонок

        fig.tight_layout(rect=[0, 0.15, 1, 1]) # Корректировка макета, чтобы легенда поместилась снизу

        # ----- ИЗМЕНЕНИЯ ЗАВЕРШАЮТСЯ ЗДЕСЬ -----

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