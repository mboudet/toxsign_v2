import pytest

from toxsign.ontologies.tests.factories import BiologicalFactory
from toxsign.ontologies.models import Biological

pytestmark = pytest.mark.django_db

def test_project_model():
    # Warning : infinite recursiong. Set parents of parents (and ancestors) to None
    ontology = BiologicalFactory.create(name='my_ont', as_parent_as_parent=None, as_ancestor_as_ancestor=None)
    assert ontology.name == 'my_ont'
    assert len(ontology.as_parent) == 1
    assert len(ontology.as_ancestor) == 1

def test_data_load():
    ontologies = Biological.objects.all()
    assert len(ontologies) == 2497
