from django.contrib import admin
from .models import GeneralStatistic
from .models import DemandStatistic
from .models import GeographyStatistic
from .models import SkillStatistic

@admin.register(GeneralStatistic)
class GeneralStatisticAdmin(admin.ModelAdmin):
    list_display    = ('name', 'title', 'created')
    readonly_fields = ('created',)
    search_fields   = ('name', 'title')

@admin.register(DemandStatistic)
class DemandStatisticAdmin(admin.ModelAdmin):
    list_display = ('name','title','created')
    readonly_fields = ('created',)

@admin.register(GeographyStatistic)
class GeographyStatisticAdmin(admin.ModelAdmin):
    list_display    = ('name', 'title', 'created')
    readonly_fields = ('created',)

@admin.register(SkillStatistic)
class SkillStatisticAdmin(admin.ModelAdmin):
    list_display    = ('name','title','created')
    readonly_fields = ('created',)
