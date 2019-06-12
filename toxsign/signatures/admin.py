from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model

from toxsign.signatures.models import Signature
class SignatureAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['name', 
        'tsx_id', 
        'created_by',
        'status',
        'signature_type',
        'phenotype_description',
        'experimental_design',
        'dev_stage',
        'generation',
        'sex_type',
        'exp_type',
        'prj_subClass',
        'std_subClass',
        'ass_subClass',
        'ftc_subClass',
        'organism',
        'tissue',
        'cell',
        'cell_ligne',
        'chemical',
        'chemical_slug',
        'disease',
        'technology',
        'technology_slug',
        'platform',
        'control_sample_number',
        'treated_sample_number',
        'pvalue',
        'cutoff',
        'statistical_processing',
        'up_gene_file_path',
        'down_gene_file_path',
        'interrogated_gene_file_path',
        'additional_file_path',
        'gene_id',
    ]}),
    ]
    list_display = ['name', 'created_at', 'updated_at']
    search_fields = ['name']

admin.site.register(Signature, SignatureAdmin)
