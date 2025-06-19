from django.urls import path
from .views import GeneralStatsView, DemandView, GeographyView

app_name = 'stats'

urlpatterns = [
    path('charts/', GeneralStatsView.as_view(), name='general_stats'),
    path('demand/', DemandView.as_view(), name='demand'),
    path('geography/', GeographyView.as_view(),   name='geography')
]
