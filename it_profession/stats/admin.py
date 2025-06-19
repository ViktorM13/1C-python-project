from django.contrib import admin
from .models import GeneralStatistic
from .models import DemandStatistic

@admin.register(GeneralStatistic)
class GeneralStatisticAdmin(admin.ModelAdmin):
    list_display    = ('name', 'title', 'created')
    readonly_fields = ('created',)
    search_fields   = ('name', 'title')

@admin.register(DemandStatistic)
class DemandStatisticAdmin(admin.ModelAdmin):
    list_display = ('name','title','created')
    readonly_fields = ('created',)