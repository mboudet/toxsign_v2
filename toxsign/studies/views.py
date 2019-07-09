from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import generic
from django.views.generic import DetailView, ListView, RedirectView, UpdateView

from toxsign.studies.models import Study

User = get_user_model()

class DetailView(LoginRequiredMixin, DetailView):
    template_name = 'studies/details.html'
    model = Study
    context_object_name = 'study'

    def get_object(self, queryset=None):
            return Study.objects.get(tsx_id=self.kwargs['stdid'])

class EditView(LoginRequiredMixin, UpdateView):

    model = Study
    template_name = 'studies/study_edit.html'
    fields = ["name", "description"]
    context_object_name = 'edit'

    def get_object(self, queryset=None):
        return Study.objects.get(pk=self.kwargs['pk'])
