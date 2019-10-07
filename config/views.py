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

from toxsign.superprojects.models import Superproject
from toxsign.assays.models import Assay, Factor
from toxsign.projects.models import Project
from toxsign.signatures.models import Signature
from toxsign.projects.views import check_view_permissions, check_edit_permissions

from toxsign.superprojects.documents import SuperprojectDocument
from toxsign.projects.documents import ProjectDocument
from toxsign.signatures.documents import SignatureDocument
from toxsign.ontologies.documents import *
from elasticsearch_dsl import Q as Q_es

from django.template.loader import render_to_string
from . import forms
from django.http import JsonResponse

def HomeView(request):
        context = {}
        return render(request, 'pages/home.html',context)

def autocompleteModel(request):
    query = request.GET.get('q')

    try:
        # Wildcard for search (not optimal)
        query = "*" + query + "*"
        if request.user.is_authenticated:
            groups = [group.id for group in request.user.groups.all()]
            q = Q_es("match", created_by__username=request.user.username)  | Q_es("match", status="PUBLIC") | Q_es('nested', path="read_groups", query=Q_es("terms", read_groups__id=groups))
        else:
            q = Q_es("match", status="PUBLIC")

        allowed_projects =  ProjectDocument.search().query(q)
        # Limit all query to theses projects
        allowed_projects_id_list = [project.id for project in allowed_projects]

        # Now do the queries
        results_superprojects = SuperprojectDocument.search()
        results_projects = allowed_projects
        results_signatures = SignatureDocument.search().filter("terms", factor__assay__project__id=allowed_projects_id_list)

        # This search in all fields.. might be too much. Might need to restrict to fields we actually show on the search page..
        q = Q_es("query_string", query=query)

        results_superprojects = results_superprojects.filter(q)
        superprojects_number = results_superprojects.count()
        results_superprojects = results_superprojects.scan()
        results_projects = results_projects.filter(q)
        projects_number = results_projects.count()
        results_projects = results_projects.scan()

        results_signatures = results_signatures.filter(q)
        signatures_number = results_signatures.count()
        results_signatures = results_signatures.scan()

    # Fallback to DB search
    # Need to select the correct error I guess
    except Exception as e:

        results_superprojects = Superproject.objects.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(tsx_id__icontains=query))
        results_projects = Project.objects.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(tsx_id__icontains=query))
        results_signatures = Signature.objects.filter(Q(name__icontains=query) | Q(tsx_id__icontains=query))

        results_projects = [project for project in results_projects if check_view_permissions(request.user, project)]
        results_signatures = [sig for sig in results_signatures if check_view_permissions(request.user, sig.factor.assay.project)]
        superprojects_number = len(results_superprojects)
        projects_number =  len(results_projects)
        signatures_number = len(results_signatures)

    results = {
        'superprojects_number' : superprojects_number,
        'projects_number' : projects_number,
        'signatures_number' : signatures_number,
        'superprojects' : results_superprojects,
        'projects': results_projects,
        'signatures': results_signatures
    }
    return render(request, 'pages/ajax_search.html', {'status': results})

def advanced_search_form(request):

    if request.method == 'POST':
        data = request.POST
        terms = json.loads(data['terms'])
        entity = data['entity']
        context = {}
        data = {}
        if entity == 'project':
            context['projects'] = search(request, Project, ProjectDocument, entity, terms)

        elif entity == "signature":
            context['signatures'] = search(request, Signature, SignatureDocument, entity, terms)


        data['html_page'] = render_to_string('pages/partial_advanced_search.html',
            context,
            request=request,
        )
        return JsonResponse(data)

    else:
        entity_type = request.GET.get('entity')
        data = {}
        if entity_type == 'project':
            form = forms.ProjectSearchForm()
        elif entity_type == 'signature':
            form = forms.SignatureSearchForm()

        context = {'form': form}
        data['html_form'] = render_to_string('pages/advanced_search_form.html',
            context,
            request=request,
        )
        return JsonResponse(data)

    return None

def graph_data(request):

    query = request.GET.get('q')
    project = Project.objects.get(tsx_id=query)
    if not check_view_permissions(request.user, project):
        return JsonResponse({"data" : {}, "max_parallel":0, max_depth: "0"}, safe=False)

    editable = check_edit_permissions(request.user, project)

    response = {
        'name': project.name,
        'type': 'project',
        'tsx_id': project.tsx_id,
        'view_url': project.get_absolute_url(),
        'create_url': get_sub_create_url('project', project.tsx_id, project.tsx_id),
        'edit_url': get_edit_url('project', project.tsx_id),
        'clone_url': get_clone_url('project', project.tsx_id, project.tsx_id),
        'self_editable': check_edit_permissions(request.user, project, True),
        'editable': editable
    }
    sign_count = 0
    assay_count = 0
    factor_count = 0

    assay_list = []
    for assay in project.assay_of.all():
        factor_list = []
        for factor in assay.factor_of.all():
            signature_list = []
            for signature in factor.signature_of_of.all():
                sign_count +=1
                signature_list.append({'name': signature.name, 'type': 'signature', 'tsx_id': signature.tsx_id, 'view_url': signature.get_absolute_url(),
                                      'create_url': {}, 'clone_url': get_clone_url('signature', project.tsx_id, signature.tsx_id),
                                      'edit_url': get_edit_url('signature', signature.tsx_id), 'editable': editable, 'self_editable': editable})
            factor_count += 1
            factor_list.append({'name': factor.name, 'children': signature_list, 'type': 'factor', 'tsx_id': factor.tsx_id, 'view_url': factor.get_absolute_url(),
                          'create_url': get_sub_create_url('factor', project.tsx_id, factor.tsx_id),
                          'clone_url': get_clone_url('factor', project.tsx_id, factor.tsx_id),
                          'edit_url': get_edit_url('factor', factor.tsx_id), 'editable': editable, 'self_editable': editable,
                          'count_subentities': count_subentities(factor, 'factor'),
                          'subentities': [{'name' : 'subfactors', 'is_modal': True,
                            'view_url': reverse('assays:factor_subfactor_detail', kwargs={'facid': factor.tsx_id})}]})
        assay_count +=1
        assay_list.append({'name': assay.name, 'children': factor_list, 'type': 'assay', 'tsx_id': assay.tsx_id, 'view_url': assay.get_absolute_url(),
                          'create_url': get_sub_create_url('assay', project.tsx_id, assay.tsx_id),
                          'clone_url': get_clone_url('assay', project.tsx_id, assay.tsx_id),
                          'edit_url': get_edit_url('assay', assay.tsx_id), 'editable': editable, 'self_editable': editable})

    response['children'] = assay_list

    data = {
        "data": response,
        "max_parallel": max(assay_count, sign_count, 1),
        "max_depth": 4
    }

    return JsonResponse(data, safe=False)

def index(request):

    superprojects = Superproject.objects.all()
    all_projects = Project.objects.all().order_by('id')
    projects = []
    assays = []
    signatures = []

    # TODO (Maybe?) -> Show index from elasticsearch : need fallback
    # Below : tentative implementation for projects and studies

    #  !!!!! WARNING: 'terms' query does not work on tsx_id fields (it works on id fields) !!!!!

    #if request.user.is_authenticated:
    #    groups = [group.id for group in request.user.groups.all()]
    #    q = Q_es('nested', path="read_groups", query=Q_es("terms", read_groups__id=groups)) | Q_es("match", status="PUBLIC")
    #else:
    #    q = Q_es("match", status="PUBLIC")
        # Should use ES for pagination..
        # Need to convert it to list for it to work with paginator...
    #project_list =  ProjectDocument.search().query(q).scan()
    #project_id_list = []
    #for project in project_list:
    #    projects.append(project)
    #    project_id_list.append(project.id)
    #q = Q_es("terms", project__id=project_id_list)
    #studies = StudyDocument().search().query(q).scan()
    #studies = [study for study in studies]

    for project in all_projects:
        if check_view_permissions(request.user, project):
                # Might be better to loop around than to request.
            projects.append(project)
            assays = assays + [ assay for assay in Assay.objects.filter(project=project)]
            signatures = signatures + [ signature for signature in Signature.objects.filter(factor__assay__project=project)]

    paginator = Paginator(superprojects, 5)
    page = request.GET.get('superprojects')
    try:
        superprojects = paginator.page(page)
    except PageNotAnInteger:
        superprojects = paginator.page(1)
    except EmptyPage:
        superprojects = paginator.page(paginator.num_pages)

    paginator = Paginator(projects, 5)
    page = request.GET.get('projects')
    try:
        projects = paginator.page(page)
    except PageNotAnInteger:
        projects = paginator.page(1)
    except EmptyPage:
        projects = paginator.page(paginator.num_pages)

    paginator = Paginator(assays, 6)
    page = request.GET.get('assays')
    try:
        assays = paginator.page(page)
    except PageNotAnInteger:
        assays = paginator.page(1)
    except EmptyPage:
        assays = paginator.page(paginator.num_pages)

    paginator = Paginator(signatures, 6)
    page = request.GET.get('signatures')
    try:
        signatures = paginator.page(page)
    except PageNotAnInteger:
        signatures = paginator.page(1)
    except EmptyPage:
        signatures = paginator.page(paginator.num_pages)

    context = {
        'superproject_list': superprojects,
        'project_list': projects,
        'assay_list': assays,
        'signature_list': signatures,
    }

    return render(request, 'pages/index.html', context)

def get_sub_create_url(entity_type, prj_id, tsx_id):
    query = "?selected=" + tsx_id

    if entity_type == 'project':
        return {'assay': reverse('assays:assay_create', kwargs={'prjid': prj_id}) + query}
    elif entity_type == 'assay':
        return {'factor': reverse('assays:factor_create', kwargs={'prjid': prj_id}) + query}
    elif entity_type == 'factor':
        return {'signature': reverse('signatures:signature_create', kwargs={'prjid': prj_id}) + query}

def get_clone_url(entity_type, prj_id, tsx_id):

    query = "?clone=" + tsx_id

    if entity_type == 'project':
        return reverse('projects:project_create') + query
    elif entity_type == 'assay':
        return reverse('assays:assay_create', kwargs={'prjid': prj_id}) + query
    elif entity_type == 'factor':
        return reverse('assays:factor_create', kwargs={'prjid': prj_id}) + query
    elif entity_type == 'signature':
        return reverse('signatures:signature_create', kwargs={'prjid': prj_id}) + query

def get_edit_url(entity_type, tsx_id):

    if entity_type == 'project':
        return reverse('projects:project_edit', kwargs={'prjid': tsx_id})
    elif entity_type == 'assay':
        return reverse('assays:assay_edit', kwargs={'assid': tsx_id})
    elif entity_type == 'factor':
        return reverse('assays:factor_edit', kwargs={'facid': tsx_id})
    elif entity_type == 'signature':
        return reverse('signatures:signature_edit', kwargs={'sigid': tsx_id})

def render_403(request):
    if request.GET.get('edit'):
        action = "edit"
        split = request.GET.get('edit').split('/')
        type = split[1]
    elif request.GET.get('create'):
        action = "create"
        split = request.GET.get('create').split('/')
        type = split[1]
    else:
        action = "view"
        type = ""
    data = {
        'action': action,
        'type': type
    }

    return render(request, '403.html', {'data':data})

def search(request, model, document, entity, search_terms):

    # First try with elasticsearch, then fallback to  DB query if it fails
    try:
        # Wildcard for search
        if request.user.is_authenticated:
            groups = [group.id for group in request.user.groups.all()]
            q = Q_es("match", created_by__username=request.user.username)  | Q_es("match", status="PUBLIC") | Q_es('nested', path="read_groups", query=Q_es("terms", read_groups__id=groups))
        else:
            q = Q_es("match", status="PUBLIC")

        allowed_projects =  ProjectDocument.search().query(q)
        # Limit all query to theses projects
        allowed_projects_id_list = [project.id for project in allowed_projects]

        query = generate_query(search_terms)
        # Now do the queries
        if entity == 'project':
            results = allowed_projects
        elif entity == "signature":
            results = SignatureDocument.search().filter("terms", factor__assay__project__id=allowed_projects_id_list)

        if query:
            results = results.filter(query)

        return results

    except Exception as e:
        raise e

def generate_query(search_terms):

    # Need a dict to link the fields to the correct document
    documentDict = {
        "biological": BiologicalDocument,
        "cellline": CellLineDocument,
        "cell": CellDocument,
        "chemical": ChemicalDocument,
        "disease": DiseaseDocument,
        "experiment": ExperimentDocument,
        "organism": SpeciesDocument,
        "tissue": TissueDocument
    }

    for index, item in enumerate(search_terms):
            # TODO : Refactor
            if index == 0:
                # Couldn't make double nested query work, so first query the correct ontologies, then query the correct signatures
                if item['is_ontology']:
                    if item['ontology_options']['search_type'] == "CHILDREN":
                        q = Q_es("match", id=item['ontology_options']['id'])
                        children_list =  [ontology.as_children for ontology in documentDict[item['arg_type']].search().query(q)][0].split(",")
                        onto_query = q | Q_es("terms", onto_id=children_list)
                    else:
                        onto_query = Q_es("match", id=item['ontology_options']['id'])

                    ontology_list = [ontology.id for ontology in documentDict[item['arg_type']].search().query(onto_query).scan()]
                    id_field = item['arg_type'] + "__id"
                    query = Q_es("nested", path=item['arg_type'], query=Q_es("terms", **{id_field:ontology_list}))

                else:
                    query = Q_es("wildcard", **{item['arg_type']:item['arg_value']})
            else:
                if item['is_ontology']:
                    if item['ontology_options']['search_type'] == "CHILDREN":
                        q = Q_es("match", id=item['ontology_options']['id'])
                        children_list =  [ontology.as_children for ontology in documentDict[item['arg_type']].search().query(q)][0].split(",")
                        onto_query = q | Q_es("terms", onto_id=children_list)
                    else:
                        onto_query = Q_es("match", id=item['ontology_options']['id'])

                    ontology_list = [ontology.id for ontology in documentDict[item['arg_type']].search().query(onto_query).scan()]
                    id_field = item['arg_type'] + "__id"
                    new_query = Q_es("nested", path=item['arg_type'], query=Q_es("terms", **{id_field:ontology_list}))

                else:
                    new_query = Q_es("wildcard", **{item['arg_type']:item['arg_value']})

                if item['bool_type'] == "AND":
                    query = query & new_query
                else:
                    query = query | new_query
    return query

def count_subentities(entity, entity_type):
    # Might use it for other entity types later on
    count = 0
    if entity_type == "factor":
        count += entity.chemical_subfactor_of.count()
    return count
