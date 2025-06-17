from django.urls import path
from .views import GeneralStatsView

app_name = 'stats'

urlpatterns = [
    path('', GeneralStatsView.as_view(), name='general_stats'),
]
