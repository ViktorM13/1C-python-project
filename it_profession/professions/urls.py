from django.urls import path
from . import views

app_name = 'professions'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('geography/', views.GeographyView.as_view(), name='geography'),
    path('skills/', views.SkillsView.as_view(), name='skills'),
    path('latest/', views.LatestJobsView.as_view(), name='latest_jobs'),
]