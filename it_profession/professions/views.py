from django.utils import timezone
from datetime import timedelta
from django.views.generic import TemplateView
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView
from .forms import RussianUserCreationForm, CustomAuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.shortcuts import redirect

from .models import HHVacancy
from .models import PageContent

class IndexView(TemplateView):
    login_url = 'login'
    template_name = 'professions/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page'] = PageContent.objects.get(slug='home')
        return ctx

class LatestJobsView(LoginRequiredMixin, TemplateView):
    login_url = 'login'
    template_name = 'professions/latest_jobs.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        since = timezone.now() - timedelta(hours=24)
        ctx['vacancies'] = (
            HHVacancy.objects
            .filter(published_at__gte=since)
            .order_by('-published_at')[:10]
        )
        return ctx

class RegisterView(CreateView):
    form_class = RussianUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('professions:index') 

    def form_valid(self, form):
        response = super().form_valid(form)

        user = self.object

        login(self.request, user)

        return response

class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'registration/login.html'
    success_url = reverse_lazy('professions:index')