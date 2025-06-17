from django.contrib import admin
from .models import HHVacancy
from .models import PageContent

@admin.register(HHVacancy)
class HHVacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'region', 'published_at')
    search_fields = ('title', 'company', 'region')
    list_filter = ('region',)

@admin.register(PageContent)
class PageContentAdmin(admin.ModelAdmin):
    list_display  = ('slug', 'title')
    search_fields = ('slug', 'title')