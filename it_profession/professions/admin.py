from django.contrib import admin
from .models import HHVacancy

@admin.register(HHVacancy)
class HHVacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'region', 'published_at')
    search_fields = ('title', 'company', 'region')
    list_filter = ('region',)
