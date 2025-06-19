from django.urls import path
from . import views

app_name = 'professions'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('latest/', views.LatestJobsView.as_view(), name='latest_jobs'),
]