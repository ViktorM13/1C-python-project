from django.db import models

class HHVacancy(models.Model):
    title        = models.CharField('Название вакансии', max_length=255)
    description  = models.TextField('Описание вакансии')
    skills       = models.TextField('Навыки (через запятую)', blank=True)
    company      = models.CharField('Компания', max_length=255, blank=True)
    salary       = models.CharField('Оклад', max_length=100, blank=True)
    currency     = models.CharField('Валюта', max_length=10, blank=True)
    region       = models.CharField('Регион', max_length=255, blank=True)
    published_at = models.DateTimeField('Дата публикации')
    url          = models.URLField('Ссылка на вакансию', max_length=500, unique=True)

    class Meta:
        verbose_name = 'Вакансия HH'
        verbose_name_plural = 'Вакансии HH'
        ordering = ['-published_at']

    def __str__(self):
        return f"{self.title} — {self.company} ({self.published_at:%Y-%m-%d %H:%M})"

class PageContent(models.Model):
    slug  = models.SlugField(max_length=50, unique=True, help_text="Уникальный идентификатор страницы, например 'home'")
    title = models.CharField(max_length=100, help_text="Заголовок страницы, выводится в теге h2")
    body  = models.TextField(help_text="HTML‑контент страницы, можно вставлять p, img и т.д.")

    class Meta:
        verbose_name = "Контент страницы"
        verbose_name_plural = "Контент для страниц"

    def __str__(self):
        return self.slug
