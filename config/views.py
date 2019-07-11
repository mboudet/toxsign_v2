from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import generic
from django.views.generic import DetailView, ListView, RedirectView, UpdateView
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


import json

from toxsign.assays.models import Assay, Factor
from toxsign.projects.models import Project
from toxsign.signatures.models import Signature
from toxsign.studies.models import Study




def HomeView(request):
        context = {}
        return render(request, 'pages/home.html',context)

def autocompleteModel(request):
    query = request.GET.get('q')
    results_projects = Project.objects.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(tsx_id__icontains=query))
    results_studies = Study.objects.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(tsx_id__icontains=query))
    results_signatures = Signature.objects.filter(Q(name__icontains=query) | Q(tsx_id__icontains=query))
    results = {
        'projects_number' : len(results_projects),
        'studies_number' : len(results_studies),
        'signatures_number' : len(results_signatures),
        'projects': results_projects,
        'studies': results_studies,
        'signatures': results_signatures
    }
    return render(request, 'pages/ajax_search.html', {'statuss': results})

def graph_data(request):
    # Need to check permissions for entities

    query = request.GET.get('q')
    project = Project.objects.get(tsx_id=query)
    studies = project.study_of.all()

    response = {
        'name': project.name,
    }

    study_list = []
    for study in studies:
        assay_list = []
        for assay in study.assay_of.all():
            factor_list = []
            for factor in assay.factor_of.all():
                signature_list = []
                for signature in factor.signature_of_of.all():
                    signature_list.append(signature.name)
                factor_list.append({'name': factor.name, 'children': signature_list})
            assay_list.append('name': assay.name, 'children': factor_list)
        study_list.append('name': study.name, 'children': assay_list)
    response['children'] = study_list
    return JsonResponse(response, safe=False)

def index(request):
    projects = Project.objects.all()
    project_number = len(projects)
    paginator = Paginator(projects, 5)
    page = request.GET.get('projects')
    try:
        projects = paginator.page(page)
    except PageNotAnInteger:
        projects = paginator.page(1)
    except EmptyPage:
        projects = paginator.page(paginator.num_pages)

    studies = Study.objects.all()
    study_number = len(studies)
    paginator = Paginator(studies, 6)
    page = request.GET.get('studies')
    try:
        studies = paginator.page(page)
    except PageNotAnInteger:
        studies = paginator.page(1)
    except EmptyPage:
        studies = paginator.page(paginator.num_pages)

    assays = Assay.objects.all()
    assay_number = len(assays)
    paginator = Paginator(assays, 6)
    page = request.GET.get('assays')
    try:
        assays = paginator.page(page)
    except PageNotAnInteger:
        assays = paginator.page(1)
    except EmptyPage:
        assays = paginator.page(paginator.num_pages)

    signatures = Signature.objects.all()
    signature_number = len(signatures)
    paginator = Paginator(signatures, 6)
    page = request.GET.get('signatures')
    try:
        signatures = paginator.page(page)
    except PageNotAnInteger:
        signatures = paginator.page(1)
    except EmptyPage:
        signatures = paginator.page(paginator.num_pages)

    context = {
        'project_list': projects,
        'study_list': studies,
        'assay_list': assays,
        'signature_list': signatures,
        'project_number':project_number,
        'study_number': study_number,
        'assay_number': assay_number,
        'signature_number': signature_number
    }

    return render(request, 'pages/index.html', context)


def search(request,query):
    print(query)
    search_qs = Project.objects.filter(name__contains=query)
