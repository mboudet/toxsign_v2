from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout
from crispy_forms.bootstrap import FormActions
from toxsign.signatures.models import Signature



class SignatureCreateForm(forms.ModelForm):

    class Meta:
        model = Signature
        exclude = ("tsx_id", "created_at", "created_by", "updated_at", "study", )

    def __init__(self, *args, **kwargs):
        super(SignatureCreateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_method = 'POST'
        self.helper.add_input(Submit('save', 'Save'))
