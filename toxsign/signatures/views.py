from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import generic
from django.views.generic import CreateView, DetailView, ListView, RedirectView, UpdateView
from django.contrib.auth.decorators import login_required

from guardian.mixins import PermissionRequiredMixin

from toxsign.projects.views import check_view_permissions
from toxsign.projects.models import Project
from toxsign.assays.models import Assay, Factor
from toxsign.signatures.models import Signature
from toxsign.signatures.forms import SignatureCreateForm, SignatureEditForm
from toxsign.users.models import User

def DetailView(request, sigid):

    signature = get_object_or_404(Signature, tsx_id=sigid)
    factor = signature.factor
    assay = factor.assay
    study = assay.study
    project = study.project

    if not check_view_permissions(request.user, project):
        return redirect('/unauthorized')

    return render(request, 'signatures/details.html', {'project': project,'study': study, 'assay': assay, 'factor': factor, 'signature': signature})

class EditSignatureView(PermissionRequiredMixin, UpdateView):
    permission_required = 'change_project'

    model = Signature
    template_name = 'signatures/signature_edit.html'
    form_class = SignatureEditForm
    redirect_field_name="edit"
    login_url = "/unauthorized"
    context_object_name = 'edit'

    def get_permission_object(self):
        self.signature = Signature.objects.get(tsx_id=self.kwargs['sigid'])
        self.project = self.signature.factor.assay.study.project
        return self.project

    def get_object(self, queryset=None):
        return self.signature

    def get_form_kwargs(self):
        kwargs = super(EditSignatureView, self).get_form_kwargs()
        factors = Factor.objects.filter(assay__study__project = self.project)
        kwargs.update({'factor': factors})
        return kwargs

class CreateSignatureView(PermissionRequiredMixin, CreateView):

    permission_required = 'change_project'
    login_url = "/unauthorized"
    redirect_field_name = "create"
    model = Signature
    form_class = SignatureCreateForm
    template_name = 'signatures/entity_create.html'

    def get_permission_object(self):
        self.project = Project.objects.get(tsx_id=self.kwargs['prjid'])
        return self.project

    def get_form_kwargs(self):

        kwargs = super(CreateSignatureView, self).get_form_kwargs()

        if self.request.GET.get('selected'):
            factors = Factor.objects.filter(tsx_id=self.request.GET.get('selected'))
            if factors.exists():
                factor = factors.all()
                kwargs.update({'factor': factor})
            else:
                factors = Factor.objects.filter(assay__study__project = self.project)
                kwargs.update({'factor': factors})
        else:
            factors = Factor.objects.filter(assay__study__project = self.project)
            kwargs.update({'factor': factors})


        if self.request.GET.get('clone'):
            sigs = Signature.objects.filter(tsx_id=self.request.GET.get('clone'))
            if sigs.exists():
                sig = sigs.first()
                kwargs.update({'sig': sig})

        return kwargs

    # Autofill the user
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.created_by = User.objects.get(id=self.request.user.id)
        return super(CreateView, self).form_valid(form)
