from django.contrib import admin
from .models import GeneralStatistic

@admin.register(GeneralStatistic)
class GeneralStatisticAdmin(admin.ModelAdmin):
    list_display    = ('name', 'title', 'created')
    readonly_fields = ('created',)
    search_fields   = ('name', 'title')
