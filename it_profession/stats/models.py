from django.db import models

class GeneralStatistic(models.Model):
    name        = models.SlugField(max_length=50, unique=True, verbose_name="Системное имя")
    title       = models.CharField(max_length=200, verbose_name="Заголовок")
    table_html  = models.TextField(verbose_name="HTML‑таблица")
    chart_image = models.ImageField(upload_to='statistics/charts/', verbose_name="График")
    created     = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Блок статистики"
        verbose_name_plural = "Общая статистика"
        ordering = ['name']

    def __str__(self):
        return self.title

class DemandStatistic(models.Model):
    name        = models.SlugField(max_length=50, unique=True, verbose_name="Системное имя (slug)")
    title       = models.CharField(max_length=200, verbose_name="Заголовок блока")
    table_html  = models.TextField(verbose_name="HTML‑таблица")
    chart_image = models.ImageField(upload_to='statistics/demand/', verbose_name="График")
    created     = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    class Meta:
        verbose_name = "Блок востребованности"
        verbose_name_plural = "Востребованность"
        ordering = ['name']
    def __str__(self):
        return self.title
